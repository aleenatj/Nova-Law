from enum import Enum


class UserRoleEnum(str, Enum):
    """User role enumeration with hierarchy and display names."""

    NAVIGATOR = "Navigator"
    LAWYER = "Lawyer"
    CUSTOMER = "Customer"

    @property
    def id(self) -> int:
        """Get the role ID."""
        id_mapping = {
            "Navigator": 1,
            "Lawyer": 2,
            "Customer": 3
        }
        return id_mapping[self.value]

    @property
    def hierarchy(self) -> int:
        """Get the role hierarchy level."""
        hierarchy_mapping = {
            "Navigator": 100,
            "Lawyer": 50,
            "Customer": 10
        }
        return hierarchy_mapping[self.value]

    @property
    def display_name(self) -> str:
        """Get the display name."""
        return self.value

    @classmethod
    def from_id(cls, id_: int) -> "UserRoleEnum":
        """Get role enum from ID."""
        id_to_role = {
            1: cls.NAVIGATOR,
            2: cls.LAWYER,
            3: cls.CUSTOMER
        }
        if id_ not in id_to_role:
            raise Exception("Invalid role id")
        return id_to_role[id_]

    @classmethod
    def from_code(cls, code: str) -> "UserRoleEnum":
        """Get role enum from code."""
        code_to_role = {
            "Navigator": cls.NAVIGATOR,
            "Lawyer": cls.LAWYER,
            "Customer": cls.CUSTOMER
        }
        return code_to_role[code]
