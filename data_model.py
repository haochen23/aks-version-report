from dataclasses import dataclass, field

automation_account_map = {
    # PRE-PROD
    "e32853a6-b14b-4222-a8da-7f53c6b5c371": {
        "Platforrms-PreProd-RG-001": ["PlatforrmsOp-PreProd-AA-001"],
        "Platforrms-PreProd-RG-002": ["PlatforrmsOp-PreProd-AA-002"]
    },
    # PROD
    "e9105e32-8664-4937-a1b8-e8a82f240d54": {
        "Platforms-Prod-RG-001": ["PlatforrmsOp-Prod-AA-001"]
    },
    # SHARED
    "8ab21e60-6a27-4526-99f0-79e8395957f3": {
        "Platforms-Shared-RG-001": ["PlatforrmsOp-Shared-AA-001"],
        "Platforms-Shared-RG-002": ["PlatforrmsOp-Shared-AA-002"]
    }
}


@dataclass(frozen=False)
class Resource:
    Location: str
    Name: str
    Repo: str
    Type: str
    ResourceGroup: str
    Subscription: str
    Id: str
    alerts: field(default_factory=list)
    alerts_count: int


@dataclass
class VMResource(Resource):
    osType: str
    osName: str
    osVersion: str
    isBackedUp: bool
    lastbackup: str
    lastBackup_status: str
    lastRecoveryPoint: str
    protection_status: str
    policy_name: str
    backupItemid: str
    PowerStatus: str
    offer: str
    publisher: str
    sku: str
    RSV: str


@dataclass
class SQLVMResource(Resource):
    policy_name: str
    RSV: str
    protection_status: str
    lastBackup_status: str
    lastbackup: str
    vmSize: str
    isBackedUp: str
