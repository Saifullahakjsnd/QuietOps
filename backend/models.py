from typing import Literal
from pydantic import BaseModel, Field

Kind = Literal['inventory', 'sales', 'orders', 'invoices']

class Mapping(BaseModel):
    kind: Kind
    columns: dict[str, str]
    date_format: Literal['iso', 'dayfirst', 'monthfirst'] = 'iso'
    currency: str = Field(default='USD', pattern=r'^[A-Z]{3}$')

class Evidence(BaseModel):
    id: str
    dataset_id: str
    file: str
    sheet: str
    row: int
    cells: dict[str, str]
    values: dict
    description: str = ''

class DataQualityIssue(BaseModel):
    id: str
    dataset_id: str
    file: str
    row: int
    field: str
    cell: str
    value: str
    message: str
    severity: str = 'error'

class Dataset(BaseModel):
    id: str
    name: str
    sheet: str
    sha256: str
    headers: list[str]
    row_count: int
    confirmed: bool = False
    synthetic: bool = False
    kind: str | None = None
    mapping: dict | None = None

class DetectedIssue(BaseModel):
    id: str
    kind: str
    title: str
    subject: str
    supplier: str
    severity: Literal['high', 'medium', 'low']
    summary: str
    calculation: str
    assumptions: list[str]
    facts: dict
    evidence: list[Evidence]
    status: str = 'open'
    ai: dict | None = None

class AIExplanation(BaseModel):
    explanation: str = Field(min_length=15, max_length=1800)
    next_step: str = Field(min_length=10, max_length=1000)
    evidence_ids: list[str] = Field(min_length=1, max_length=8)

class ActionProposal(BaseModel):
    id: str
    issue_id: str
    title: str
    body: str
    status: str = 'draft'
    model: str
    evidence_ids: list[str]

class Decision(BaseModel):
    decision: Literal['approved', 'rejected']
    body: str | None = Field(default=None, max_length=10000)

class AuditEvent(BaseModel):
    id: str
    at: str
    action: str
    detail: str

class ScanRequest(BaseModel):
    as_of: str | None = None

class Correction(BaseModel):
    dataset_id: str
    row: int = Field(ge=2)
    field: str
    proposed_value: str = Field(max_length=500)
    reason: str = Field(min_length=3, max_length=1000)
