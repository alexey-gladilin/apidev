from pathlib import Path
from typing import Protocol

from apidev.core.models.contract_document import ContractDocument


class ContractDocumentLoaderPort(Protocol):
    def load_documents(self, contracts_root: Path) -> list[ContractDocument]: ...
