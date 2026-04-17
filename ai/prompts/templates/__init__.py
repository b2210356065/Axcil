"""Sektörel prompt şablonları."""
from ai.prompts.templates.accounting import AccountingPrompts
from ai.prompts.templates.inventory import InventoryPrompts
from ai.prompts.templates.hr_payroll import HRPayrollPrompts
from ai.prompts.templates.construction import ConstructionPrompts

__all__ = [
    "AccountingPrompts",
    "InventoryPrompts",
    "HRPayrollPrompts",
    "ConstructionPrompts",
]
