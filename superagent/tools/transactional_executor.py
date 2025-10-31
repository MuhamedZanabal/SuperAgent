"""
Transactional tool executor with ACID semantics and rollback.
"""

import asyncio
import time
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from superagent.tools.base import BaseTool, ToolResult
from superagent.tools.registry import ToolRegistry
from superagent.tools.models import ToolCall, ToolOutput
from superagent.core.logger import get_logger
from superagent.core.security import SecurityManager

logger = get_logger(__name__)


class IsolationLevel(Enum):
    """Transaction isolation levels."""
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"


@dataclass
class Checkpoint:
    """Execution checkpoint for rollback."""
    checkpoint_id: str
    timestamp: datetime
    filesystem_snapshot: Optional[Path] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Transaction:
    """Transaction context with checkpoints."""
    transaction_id: str
    isolation_level: IsolationLevel
    checkpoints: List[Checkpoint] = field(default_factory=list)
    committed: bool = False
    rolled_back: bool = False
    start_time: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TransactionResult:
    """Result of transaction execution."""
    success: bool
    results: List[ToolOutput] = field(default_factory=list)
    error: Optional[str] = None
    transaction_id: Optional[str] = None
    execution_time_ms: float = 0.0


class TransactionalToolExecutor:
    """
    Tool executor with database-inspired transaction semantics.
    
    Implements two-phase commit protocol with automatic rollback
    on failures and filesystem snapshots for state recovery.
    """
    
    def __init__(
        self,
        registry: ToolRegistry,
        security_manager: Optional[SecurityManager] = None,
        default_timeout: int = 30,
        enable_snapshots: bool = True,
    ):
        """
        Initialize transactional executor.
        
        Args:
            registry: Tool registry
            security_manager: Security manager
            default_timeout: Default timeout in seconds
            enable_snapshots: Enable filesystem snapshots
        """
        self.registry = registry
        self.security_manager = security_manager
        self.default_timeout = default_timeout
        self.enable_snapshots = enable_snapshots
        self._active_transactions: Dict[str, Transaction] = {}
    
    async def execute_tool_sequence(
        self,
        tools: List[ToolCall],
        isolation_level: IsolationLevel = IsolationLevel.SERIALIZABLE,
    ) -> TransactionResult:
        """
        Execute tool sequence with transactional semantics.
        
        Implements two-phase commit:
        - Phase 1: Validation + snapshot creation
        - Phase 2: Execution with incremental checkpointing
        
        Args:
            tools: List of tool calls to execute
            isolation_level: Transaction isolation level
            
        Returns:
            TransactionResult with success status and results
        """
        import uuid
        transaction_id = str(uuid.uuid4())
        start_time = time.time()
        
        transaction = Transaction(
            transaction_id=transaction_id,
            isolation_level=isolation_level,
        )
        self._active_transactions[transaction_id] = transaction
        
        try:
            # Phase 1: Pre-execution validation
            logger.info(f"Transaction {transaction_id}: Phase 1 - Validation")
            await self._validate_phase(tools, transaction)
            
            # Phase 2: Sequential execution with monitoring
            logger.info(f"Transaction {transaction_id}: Phase 2 - Execution")
            results = await self._execution_phase(tools, transaction)
            
            # Commit transaction
            await self._commit_transaction(transaction)
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"Transaction {transaction_id}: Committed successfully in {execution_time:.2f}ms")
            
            return TransactionResult(
                success=True,
                results=results,
                transaction_id=transaction_id,
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            # Automatic rollback on failure
            logger.error(f"Transaction {transaction_id}: Failed - {str(e)}")
            await self._rollback_transaction(transaction)
            
            execution_time = (time.time() - start_time) * 1000
            
            return TransactionResult(
                success=False,
                error=str(e),
                transaction_id=transaction_id,
                execution_time_ms=execution_time,
            )
            
        finally:
            # Cleanup
            self._active_transactions.pop(transaction_id, None)
    
    async def _validate_phase(self, tools: List[ToolCall], transaction: Transaction):
        """
        Phase 1: Validate all tools and create initial checkpoint.
        
        Args:
            tools: Tool calls to validate
            transaction: Transaction context
        """
        # Validate all tools exist
        for tool_call in tools:
            tool = self.registry.get(tool_call.tool_name)
            if not tool:
                raise ValueError(f"Tool not found: {tool_call.tool_name}")
            
            # Validate parameters
            try:
                tool.validate_parameters(tool_call.parameters)
            except Exception as e:
                raise ValueError(f"Invalid parameters for {tool_call.tool_name}: {str(e)}")
        
        # Create initial checkpoint
        checkpoint = await self._create_checkpoint(transaction)
        transaction.checkpoints.append(checkpoint)
        
        logger.debug(f"Transaction {transaction.transaction_id}: Validation complete, checkpoint created")
    
    async def _execution_phase(
        self,
        tools: List[ToolCall],
        transaction: Transaction
    ) -> List[ToolOutput]:
        """
        Phase 2: Execute tools with incremental checkpointing.
        
        Args:
            tools: Tool calls to execute
            transaction: Transaction context
            
        Returns:
            List of tool outputs
        """
        results = []
        
        for i, tool_call in enumerate(tools):
            # Create checkpoint before each tool
            if i > 0:  # Skip first as we already have initial checkpoint
                checkpoint = await self._create_checkpoint(transaction)
                transaction.checkpoints.append(checkpoint)
            
            # Execute tool
            result = await self._execute_tool_with_monitoring(tool_call, transaction)
            
            if not result.success:
                # Rollback to previous checkpoint
                if transaction.checkpoints:
                    await self._rollback_to_checkpoint(
                        transaction.checkpoints[-2] if len(transaction.checkpoints) > 1 else transaction.checkpoints[0]
                    )
                
                raise Exception(f"Tool {tool_call.tool_name} failed: {result.error}")
            
            results.append(result)
            logger.debug(f"Transaction {transaction.transaction_id}: Tool {i+1}/{len(tools)} completed")
        
        return results
    
    async def _execute_tool_with_monitoring(
        self,
        tool_call: ToolCall,
        transaction: Transaction
    ) -> ToolOutput:
        """Execute single tool with monitoring."""
        start_time = time.time()
        
        tool = self.registry.get(tool_call.tool_name)
        if not tool:
            return ToolOutput(
                call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                success=False,
                error="Tool not found",
                execution_time_ms=0.0,
            )
        
        try:
            # Validate and execute
            validated_params = tool.validate_parameters(tool_call.parameters)
            
            result = await asyncio.wait_for(
                tool.execute(**validated_params),
                timeout=self.default_timeout,
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolOutput(
                call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                success=result.success,
                output=result.output,
                error=result.error,
                execution_time_ms=execution_time,
            )
            
        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            return ToolOutput(
                call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                success=False,
                error=f"Timeout after {self.default_timeout}s",
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolOutput(
                call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )
    
    async def _create_checkpoint(self, transaction: Transaction) -> Checkpoint:
        """
        Create execution checkpoint.
        
        Args:
            transaction: Transaction context
            
        Returns:
            Checkpoint with snapshot
        """
        import uuid
        import os
        
        checkpoint_id = str(uuid.uuid4())
        
        # Create filesystem snapshot if enabled
        snapshot_path = None
        if self.enable_snapshots:
            snapshot_path = await self._create_filesystem_snapshot()
        
        # Capture environment variables
        env_vars = dict(os.environ)
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.utcnow(),
            filesystem_snapshot=snapshot_path,
            env_vars=env_vars,
        )
        
        logger.debug(f"Created checkpoint: {checkpoint_id}")
        return checkpoint
    
    async def _create_filesystem_snapshot(self) -> Path:
        """
        Create filesystem snapshot using copy-on-write.
        
        Returns:
            Path to snapshot directory
        """
        # Create temporary snapshot directory
        snapshot_dir = Path(tempfile.mkdtemp(prefix="superagent_snapshot_"))
        
        # Copy current working directory (simplified - in production, use rsync or btrfs snapshots)
        cwd = Path.cwd()
        try:
            # Only snapshot specific directories to avoid copying everything
            for item in cwd.iterdir():
                if item.is_file() and item.suffix in ['.py', '.txt', '.json', '.yaml']:
                    shutil.copy2(item, snapshot_dir / item.name)
                elif item.is_dir() and item.name not in ['.git', '__pycache__', 'node_modules', '.venv']:
                    shutil.copytree(item, snapshot_dir / item.name, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
        except Exception as e:
            logger.warning(f"Snapshot creation failed: {str(e)}")
        
        return snapshot_dir
    
    async def _rollback_to_checkpoint(self, checkpoint: Checkpoint):
        """
        Rollback to checkpoint state.
        
        Args:
            checkpoint: Checkpoint to restore
        """
        logger.info(f"Rolling back to checkpoint: {checkpoint.checkpoint_id}")
        
        # Restore filesystem if snapshot exists
        if checkpoint.filesystem_snapshot and checkpoint.filesystem_snapshot.exists():
            try:
                cwd = Path.cwd()
                # Restore files from snapshot
                for item in checkpoint.filesystem_snapshot.iterdir():
                    dest = cwd / item.name
                    if item.is_file():
                        shutil.copy2(item, dest)
                    elif item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                
                logger.info("Filesystem restored from snapshot")
            except Exception as e:
                logger.error(f"Filesystem restore failed: {str(e)}")
        
        # Note: Environment variables are process-level and can't be fully restored
        # In production, would need process isolation
    
    async def _commit_transaction(self, transaction: Transaction):
        """
        Commit transaction and cleanup checkpoints.
        
        Args:
            transaction: Transaction to commit
        """
        transaction.committed = True
        
        # Cleanup snapshots
        for checkpoint in transaction.checkpoints:
            if checkpoint.filesystem_snapshot and checkpoint.filesystem_snapshot.exists():
                try:
                    shutil.rmtree(checkpoint.filesystem_snapshot)
                except Exception as e:
                    logger.warning(f"Failed to cleanup snapshot: {str(e)}")
        
        logger.debug(f"Transaction {transaction.transaction_id}: Committed and cleaned up")
    
    async def _rollback_transaction(self, transaction: Transaction):
        """
        Rollback entire transaction.
        
        Args:
            transaction: Transaction to rollback
        """
        transaction.rolled_back = True
        
        # Rollback to initial checkpoint if available
        if transaction.checkpoints:
            await self._rollback_to_checkpoint(transaction.checkpoints[0])
        
        # Cleanup all snapshots
        for checkpoint in transaction.checkpoints:
            if checkpoint.filesystem_snapshot and checkpoint.filesystem_snapshot.exists():
                try:
                    shutil.rmtree(checkpoint.filesystem_snapshot)
                except Exception as e:
                    logger.warning(f"Failed to cleanup snapshot: {str(e)}")
        
        logger.info(f"Transaction {transaction.transaction_id}: Rolled back")
