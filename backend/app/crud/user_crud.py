"""用户数据访问层。"""

from typing import Optional

from sqlalchemy import select

from app.core.database import DatabaseManager
from app.entities.user_entity import UserEntity
from app.utils.logging.crud_logger import CrudLogger
from app.utils.password_hasher import PasswordHasher


class UserCrud:
    """用户CRUD操作类。

    提供用户数据的增删改查操作，使用异步数据库会话。
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        password_hasher: PasswordHasher,
        crud_logger: CrudLogger,
    ) -> None:
        """初始化用户CRUD。

        Args:
            db_manager: 数据库管理器实例。
            password_hasher: 密码哈希工具。
            crud_logger: CRUD日志记录器。
        """
        self._db_manager = db_manager
        self._password_hasher = password_hasher
        self._crud_logger = crud_logger

    async def get_by_student_id(self, student_id: str) -> Optional[UserEntity]:
        """根据学号获取用户。

        Args:
            student_id: 学号。

        Returns:
            用户实体或None（如果用户不存在）。
        """
        async with self._db_manager.get_session() as session:
            query = select(UserEntity).where(UserEntity.student_id == student_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                self._crud_logger.log_read(
                    "查询到用户",
                    {"student_id": student_id, "found": True},
                )
            else:
                self._crud_logger.log_read(
                    "未查询到用户",
                    {"student_id": student_id, "found": False},
                )

            return user

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """根据邮箱获取用户。

        Args:
            email: 邮箱地址。

        Returns:
            用户实体或None（如果用户不存在）。
        """
        async with self._db_manager.get_session() as session:
            query = select(UserEntity).where(UserEntity.email == email)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def update(self, user_id: int, data: dict) -> Optional[UserEntity]:
        """更新用户信息。

        Args:
            user_id: 用户ID。
            data: 更新数据。

        Returns:
            更新后的用户实体或None。
        """
        async with self._db_manager.get_session() as session:
            user = await session.get_one(UserEntity, {"id": user_id})
            if not user:
                return None
            
            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            await session.commit()
            await session.refresh(user)
            return user

    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        """根据ID获取用户。

        Args:
            user_id: 用户ID。

        Returns:
            用户实体或None（如果用户不存在）。
        """
        async with self._db_manager.get_session() as session:
            query = select(UserEntity).where(UserEntity.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                self._crud_logger.log_read(
                    "根据ID查询到用户",
                    {"user_id": user_id, "found": True},
                )
            else:
                self._crud_logger.log_read(
                    "根据ID未查询到用户",
                    {"user_id": user_id, "found": False},
                )

            return user

    async def create(
        self, student_id: str, password: str, display_name: str = None, **kwargs
    ) -> UserEntity:
        """创建新用户。

        Args:
            student_id: 学号。
            password: 明文密码（将被哈希）。
            display_name: 显示名称。
            **kwargs: 其他可选字段。

        Returns:
            创建的用户实体。
        """
        async with self._db_manager.get_session() as session:
            user = UserEntity(
                student_id=student_id,
                password_hash=self._password_hasher.hash(password),
                display_name=display_name or student_id,
                **kwargs
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)

            self._crud_logger.log_create(
                "创建用户",
                {"student_id": student_id, "display_name": display_name},
            )

            return user

    async def update_password(self, user_id: int, new_password: str) -> bool:
        """更新用户密码。

        Args:
            user_id: 用户ID。
            new_password: 新密码（明文）。

        Returns:
            是否更新成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(UserEntity).where(UserEntity.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                self._crud_logger.log_update(
                    "更新密码失败-用户不存在",
                    {"user_id": user_id, "success": False},
                )
                return False

            user.password_hash = self._password_hasher.hash(new_password)
            await session.flush()

            self._crud_logger.log_update(
                "更新用户密码",
                {"user_id": user_id, "success": True},
            )

            return True

    async def get_all_users(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[UserEntity], int]:
        """分页获取用户列表。

        Args:
            skip: 跳过的记录数。
            limit: 每页记录数。

        Returns:
            (用户列表, 总记录数) 元组。
        """
        async with self._db_manager.get_session() as session:
            # 获取总数
            from sqlalchemy import func as sql_func

            count_query = select(sql_func.count(UserEntity.id))
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            # 获取分页数据
            query = (
                select(UserEntity)
                .order_by(UserEntity.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await session.execute(query)
            users = list(result.scalars().all())

            self._crud_logger.log_read(
                "获取用户列表",
                {"skip": skip, "limit": limit, "count": len(users), "total": total},
            )

            return users, total

    async def set_active_status(self, user_id: int, is_active: bool) -> bool:
        """设置用户启用/停用状态。

        Args:
            user_id: 用户ID。
            is_active: 是否启用。

        Returns:
            是否更新成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(UserEntity).where(UserEntity.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                self._crud_logger.log_update(
                    "更新用户状态失败-用户不存在",
                    {"user_id": user_id, "success": False},
                )
                return False

            user.is_active = is_active
            await session.flush()

            self._crud_logger.log_update(
                "更新用户状态",
                {"user_id": user_id, "is_active": is_active, "success": True},
            )

            return True

    async def delete_user(self, user_id: int) -> bool:
        """删除用户。

        Args:
            user_id: 用户ID。

        Returns:
            是否删除成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(UserEntity).where(UserEntity.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                self._crud_logger.log_delete(
                    "删除用户失败-用户不存在",
                    {"user_id": user_id, "success": False},
                )
                return False

            await session.delete(user)
            await session.flush()

            self._crud_logger.log_delete(
                "删除用户",
                {"user_id": user_id, "student_id": user.student_id, "success": True},
            )

            return True

    async def get_users_by_role(
        self, role: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[UserEntity], int]:
        """根据角色分页获取用户列表。

        Args:
            role: 用户角色（user/admin/super_admin）。
            skip: 跳过的记录数。
            limit: 每页记录数。

        Returns:
            (用户列表, 总记录数) 元组。
        """
        async with self._db_manager.get_session() as session:
            from sqlalchemy import func as sql_func

            # 获取总数
            count_query = select(sql_func.count(UserEntity.id)).where(
                UserEntity.role == role
            )
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            # 获取分页数据
            query = (
                select(UserEntity)
                .where(UserEntity.role == role)
                .order_by(UserEntity.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await session.execute(query)
            users = list(result.scalars().all())

            self._crud_logger.log_read(
                "按角色获取用户列表",
                {
                    "role": role,
                    "skip": skip,
                    "limit": limit,
                    "count": len(users),
                    "total": total,
                },
            )

            return users, total

    async def get_admins(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[UserEntity], int]:
        """获取管理员列表（包括admin，不包括super_admin）。

        Args:
            skip: 跳过的记录数。
            limit: 每页记录数。

        Returns:
            (管理员列表, 总记录数) 元组。
        """
        return await self.get_users_by_role("admin", skip, limit)

    async def get_students(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[UserEntity], int]:
        """获取学生用户列表。

        Args:
            skip: 跳过的记录数。
            limit: 每页记录数。

        Returns:
            (学生用户列表, 总记录数) 元组。
        """
        return await self.get_users_by_role("user", skip, limit)

    async def create_with_role(
        self, student_id: str, password: str, display_name: str, role: str = "user"
    ) -> UserEntity:
        """创建指定角色的用户。

        Args:
            student_id: 学号。
            password: 明文密码（将被哈希）。
            display_name: 显示名称。
            role: 用户角色。

        Returns:
            创建的用户实体。
        """
        async with self._db_manager.get_session() as session:
            user = UserEntity(
                student_id=student_id,
                password_hash=self._password_hasher.hash(password),
                display_name=display_name,
                role=role,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)

            self._crud_logger.log_create(
                "创建用户",
                {"student_id": student_id, "display_name": display_name, "role": role},
            )

            return user