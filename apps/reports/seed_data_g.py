"""Seed data for Category G — Finance templates."""

from __future__ import annotations

T = "TEXT"
MT = "MULTILINE_TEXT"
RT = "RICH_TEXT"
INT = "INTEGER"
DEC = "DECIMAL"
PCT = "PERCENTAGE"
DT = "DATE"
TM = "TIME"
DD = "DROPDOWN"
CB = "CHECKBOX"
DOC = "DOCUMENT"
IMG = "IMAGE"
VID = "VIDEO"
SIG = "SIGNATURE"
USR = "USER_SELECTOR"

CATEGORY_G_TEMPLATES: list[dict] = [
    {
        "code": "G1",
        "title": "Monthly Financial Report",
        "description": "Monthly report summarizing income, expenditure and financial position.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Month", "code": "reporting_month", "field_type": DT, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                            {"label": "Reviewed By", "code": "reviewed_by", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Income",
                "code": "income",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Income",
                        "code": "income",
                        "fields": [
                            {"label": "Source", "code": "source", "field_type": T, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Budgeted", "code": "budgeted", "field_type": DEC},
                            {"label": "Actual", "code": "actual", "field_type": DEC, "required": True},
                            {"label": "Variance", "code": "variance", "field_type": DEC, "is_calculated": True, "formula": "actual - budgeted"},
                        ],
                    }
                ],
            },
            {
                "name": "Expenditure",
                "code": "expenditure",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Expenditure",
                        "code": "expenditure",
                        "fields": [
                            {"label": "Category", "code": "category", "field_type": T, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Budgeted", "code": "budgeted", "field_type": DEC},
                            {"label": "Actual", "code": "actual", "field_type": DEC, "required": True},
                            {"label": "Variance", "code": "variance", "field_type": DEC, "is_calculated": True, "formula": "actual - budgeted"},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Income", "code": "total_income", "field_type": DEC, "is_calculated": True, "formula": "sum(income.actual)"},
                            {"label": "Total Expenditure", "code": "total_expenditure", "field_type": DEC, "is_calculated": True, "formula": "sum(expenditure.actual)"},
                            {"label": "Net Balance", "code": "net_balance", "field_type": DEC, "is_calculated": True, "formula": "total_income - total_expenditure"},
                            {"label": "Bank Balance", "code": "bank_balance", "field_type": DEC},
                            {"label": "Financial Notes", "code": "financial_notes", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G2",
        "title": "Quarterly Financial Report",
        "description": "Quarterly report providing detailed financial analysis and projections.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Quarter", "code": "quarter", "field_type": DD, "options": ["Q1", "Q2", "Q3", "Q4"], "required": True},
                            {"label": "Year", "code": "year", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Income Summary",
                "code": "income-summary",
                "groups": [
                    {
                        "name": "Income Summary",
                        "code": "income-summary",
                        "fields": [
                            {"label": "Total Budgeted Income", "code": "budgeted_income", "field_type": DEC},
                            {"label": "Total Actual Income", "code": "actual_income", "field_type": DEC, "required": True},
                            {"label": "Income Variance", "code": "income_variance", "field_type": DEC, "is_calculated": True, "formula": "actual_income - budgeted_income"},
                            {"label": "Income Achievement", "code": "income_achievement", "field_type": PCT, "is_calculated": True, "formula": "actual_income / budgeted_income * 100"},
                        ],
                    }
                ],
            },
            {
                "name": "Expenditure Summary",
                "code": "expenditure-summary",
                "groups": [
                    {
                        "name": "Expenditure Summary",
                        "code": "expenditure-summary",
                        "fields": [
                            {"label": "Total Budgeted Expenditure", "code": "budgeted_expenditure", "field_type": DEC},
                            {"label": "Total Actual Expenditure", "code": "actual_expenditure", "field_type": DEC, "required": True},
                            {"label": "Expenditure Variance", "code": "expenditure_variance", "field_type": DEC, "is_calculated": True, "formula": "actual_expenditure - budgeted_expenditure"},
                            {"label": "Expenditure Achievement", "code": "expenditure_achievement", "field_type": PCT, "is_calculated": True, "formula": "actual_expenditure / budgeted_expenditure * 100"},
                        ],
                    }
                ],
            },
            {
                "name": "Financial Position",
                "code": "financial-position",
                "groups": [
                    {
                        "name": "Financial Position",
                        "code": "financial-position",
                        "fields": [
                            {"label": "Bank Balance", "code": "bank_balance", "field_type": DEC},
                            {"label": "Cash in Hand", "code": "cash_in_hand", "field_type": DEC},
                            {"label": "Receivables", "code": "receivables", "field_type": DEC},
                            {"label": "Payables", "code": "payables", "field_type": DEC},
                            {"label": "Net Position", "code": "net_position", "field_type": DEC, "is_calculated": True, "formula": "bank_balance + cash_in_hand + receivables - payables"},
                            {"label": "Quarterly Forecast", "code": "quarterly_forecast", "field_type": RT},
                            {"label": "Financial Notes", "code": "financial_notes", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G3",
        "title": "Annual Financial Statement",
        "description": "Annual financial statement including income statement and balance sheet.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Financial Year", "code": "financial_year", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                            {"label": "Approved By", "code": "approved_by", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Income Statement",
                "code": "income-statement",
                "groups": [
                    {
                        "name": "Income Statement",
                        "code": "income-statement",
                        "fields": [
                            {"label": "Grant Income", "code": "grant_income", "field_type": DEC},
                            {"label": "Donation Income", "code": "donation_income", "field_type": DEC},
                            {"label": "Program Income", "code": "program_income", "field_type": DEC},
                            {"label": "Other Income", "code": "other_income", "field_type": DEC},
                            {"label": "Total Income", "code": "total_income", "field_type": DEC, "is_calculated": True, "formula": "grant_income + donation_income + program_income + other_income"},
                        ],
                    }
                ],
            },
            {
                "name": "Expenditure Statement",
                "code": "expenditure-statement",
                "groups": [
                    {
                        "name": "Expenditure Statement",
                        "code": "expenditure-statement",
                        "fields": [
                            {"label": "Program Expenditure", "code": "program_expenditure", "field_type": DEC},
                            {"label": "Administrative Expenditure", "code": "admin_expenditure", "field_type": DEC},
                            {"label": "Fundraising Expenditure", "code": "fundraising_expenditure", "field_type": DEC},
                            {"label": "Total Expenditure", "code": "total_expenditure", "field_type": DEC, "is_calculated": True, "formula": "program_expenditure + admin_expenditure + fundraising_expenditure"},
                            {"label": "Net Surplus (Deficit)", "code": "net_surplus", "field_type": DEC, "is_calculated": True, "formula": "total_income - total_expenditure"},
                        ],
                    }
                ],
            },
            {
                "name": "Balance Sheet — Assets",
                "code": "assets",
                "groups": [
                    {
                        "name": "Balance Sheet — Assets",
                        "code": "assets",
                        "fields": [
                            {"label": "Current Assets", "code": "current_assets", "field_type": DEC},
                            {"label": "Fixed Assets", "code": "fixed_assets", "field_type": DEC},
                            {"label": "Total Assets", "code": "total_assets", "field_type": DEC, "is_calculated": True, "formula": "current_assets + fixed_assets"},
                        ],
                    }
                ],
            },
            {
                "name": "Balance Sheet — Liabilities",
                "code": "liabilities",
                "groups": [
                    {
                        "name": "Balance Sheet — Liabilities",
                        "code": "liabilities",
                        "fields": [
                            {"label": "Current Liabilities", "code": "current_liabilities", "field_type": DEC},
                            {"label": "Long-term Liabilities", "code": "long_term_liabilities", "field_type": DEC},
                            {"label": "Total Liabilities", "code": "total_liabilities", "field_type": DEC, "is_calculated": True, "formula": "current_liabilities + long_term_liabilities"},
                            {"label": "Net Assets", "code": "net_assets", "field_type": DEC, "is_calculated": True, "formula": "total_assets - total_liabilities"},
                        ],
                    }
                ],
            },
            {
                "name": "Approval",
                "code": "approval",
                "groups": [
                    {
                        "name": "Approval",
                        "code": "approval",
                        "fields": [
                            {"label": "Auditor Opinion", "code": "auditor_opinion", "field_type": RT},
                            {"label": "Signature", "code": "signature", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G4",
        "title": "Budget Performance Report",
        "description": "Report comparing actual financial performance against the approved budget.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Budget Lines",
                "code": "budget-lines",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Budget Lines",
                        "code": "budget-lines",
                        "fields": [
                            {"label": "Budget Line", "code": "budget_line", "field_type": T, "required": True},
                            {"label": "Type", "code": "type", "field_type": DD, "options": ["Income", "Expenditure"], "required": True},
                            {"label": "Annual Budget", "code": "annual_budget", "field_type": DEC},
                            {"label": "Period Budget", "code": "period_budget", "field_type": DEC},
                            {"label": "Actual", "code": "actual", "field_type": DEC, "required": True},
                            {"label": "Variance", "code": "variance", "field_type": DEC, "is_calculated": True, "formula": "actual - period_budget"},
                            {"label": "Variance Percentage", "code": "variance_pct", "field_type": PCT, "is_calculated": True, "formula": "variance / period_budget * 100"},
                            {"label": "Cumulative Actual", "code": "cumulative_actual", "field_type": DEC},
                            {"label": "Cumulative Achievement", "code": "cumulative_achievement", "field_type": PCT, "is_calculated": True, "formula": "cumulative_actual / annual_budget * 100"},
                        ],
                    }
                ],
            },
            {
                "name": "Analysis",
                "code": "analysis",
                "groups": [
                    {
                        "name": "Analysis",
                        "code": "analysis",
                        "fields": [
                            {"label": "Key Variances", "code": "key_variances", "field_type": RT, "required": True},
                            {"label": "Corrective Actions", "code": "corrective_actions", "field_type": MT},
                            {"label": "Revised Forecast", "code": "revised_forecast", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G5",
        "title": "Budget Variance Report",
        "description": "Detailed report analyzing significant budget variances and their causes.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Variances",
                "code": "variances",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Variances",
                        "code": "variances",
                        "fields": [
                            {"label": "Budget Line", "code": "budget_line", "field_type": T, "required": True},
                            {"label": "Budgeted Amount", "code": "budgeted_amount", "field_type": DEC, "required": True},
                            {"label": "Actual Amount", "code": "actual_amount", "field_type": DEC, "required": True},
                            {"label": "Variance Amount", "code": "variance_amount", "field_type": DEC, "is_calculated": True, "formula": "actual_amount - budgeted_amount"},
                            {"label": "Variance Percentage", "code": "variance_pct", "field_type": PCT, "is_calculated": True, "formula": "variance_amount / budgeted_amount * 100"},
                            {"label": "Significance", "code": "significance", "field_type": DD, "options": ["High", "Medium", "Low"], "required": True},
                            {"label": "Cause of Variance", "code": "variance_cause", "field_type": MT, "required": True},
                            {"label": "Corrective Action", "code": "corrective_action", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Variances", "code": "total_variances", "field_type": DEC},
                            {"label": "High Significance Count", "code": "high_variance_count", "field_type": INT},
                            {"label": "Management Response", "code": "management_response", "field_type": RT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G6",
        "title": "Cash Flow Report",
        "description": "Report on cash flow position and liquidity management.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Month", "code": "reporting_month", "field_type": DT, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Cash Inflows",
                "code": "cash-inflows",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Cash Inflows",
                        "code": "cash-inflows",
                        "fields": [
                            {"label": "Source", "code": "source", "field_type": T, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Expected Date", "code": "expected_date", "field_type": DT},
                            {"label": "Expected Amount", "code": "expected_amount", "field_type": DEC},
                            {"label": "Actual Amount", "code": "actual_amount", "field_type": DEC},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Received", "Pending", "Delayed"]},
                        ],
                    }
                ],
            },
            {
                "name": "Cash Outflows",
                "code": "cash-outflows",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Cash Outflows",
                        "code": "cash-outflows",
                        "fields": [
                            {"label": "Payee", "code": "payee", "field_type": T, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Due Date", "code": "due_date", "field_type": DT},
                            {"label": "Amount", "code": "amount", "field_type": DEC, "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Paid", "Pending", "Overdue"]},
                        ],
                    }
                ],
            },
            {
                "name": "Cash Position",
                "code": "cash-position",
                "groups": [
                    {
                        "name": "Cash Position",
                        "code": "cash-position",
                        "fields": [
                            {"label": "Opening Balance", "code": "opening_balance", "field_type": DEC},
                            {"label": "Total Inflows", "code": "total_inflows", "field_type": DEC, "is_calculated": True, "formula": "sum(inflow.actual_amount)"},
                            {"label": "Total Outflows", "code": "total_outflows", "field_type": DEC, "is_calculated": True, "formula": "sum(outflow.amount)"},
                            {"label": "Closing Balance", "code": "closing_balance", "field_type": DEC, "is_calculated": True, "formula": "opening_balance + total_inflows - total_outflows"},
                            {"label": "Minimum Required Balance", "code": "min_required", "field_type": DEC},
                            {"label": "Cash Flow Status", "code": "cash_flow_status", "field_type": DD, "options": ["Healthy", "Adequate", "Concern", "Critical"]},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G7",
        "title": "Income and Expenditure Report",
        "description": "Detailed report on all income and expenditure transactions.",
        "reporting_frequency": "MONTHLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Month", "code": "reporting_month", "field_type": DT, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Income Transactions",
                "code": "income-transactions",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Income Transactions",
                        "code": "income-transactions",
                        "fields": [
                            {"label": "Date", "code": "date", "field_type": DT, "required": True},
                            {"label": "Source", "code": "source", "field_type": T, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Reference", "code": "reference", "field_type": T},
                            {"label": "Amount", "code": "amount", "field_type": DEC, "required": True},
                            {"label": "Fund", "code": "fund", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Expenditure Transactions",
                "code": "expenditure-transactions",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Expenditure Transactions",
                        "code": "expenditure-transactions",
                        "fields": [
                            {"label": "Date", "code": "date", "field_type": DT, "required": True},
                            {"label": "Payee", "code": "payee", "field_type": T, "required": True},
                            {"label": "Description", "code": "description", "field_type": MT},
                            {"label": "Reference", "code": "reference", "field_type": T},
                            {"label": "Amount", "code": "amount", "field_type": DEC, "required": True},
                            {"label": "Category", "code": "category", "field_type": T},
                            {"label": "Fund", "code": "fund", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Income", "code": "total_income", "field_type": DEC, "is_calculated": True, "formula": "sum(income.amount)"},
                            {"label": "Total Expenditure", "code": "total_expenditure", "field_type": DEC, "is_calculated": True, "formula": "sum(expenditure.amount)"},
                            {"label": "Net Balance", "code": "net_balance", "field_type": DEC, "is_calculated": True, "formula": "total_income - total_expenditure"},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G8",
        "title": "Procurement Report",
        "description": "Report on procurement activities, purchases and vendor management.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Procurement Officer", "code": "procurement_officer", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Procurements",
                "code": "procurements",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Procurements",
                        "code": "procurements",
                        "fields": [
                            {"label": "Item Description", "code": "item_description", "field_type": T, "required": True},
                            {"label": "Category", "code": "category", "field_type": DD, "options": ["Goods", "Services", "Works", "Consultancy"], "required": True},
                            {"label": "Requisition Date", "code": "requisition_date", "field_type": DT},
                            {"label": "Procurement Method", "code": "procurement_method", "field_type": DD, "options": ["Direct Purchase", "Quotation", "Tender", "International"]},
                            {"label": "Vendor", "code": "vendor", "field_type": T},
                            {"label": "Amount", "code": "amount", "field_type": DEC, "required": True},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Requisitioned", "Approved", "Ordered", "Delivered", "Completed"]},
                            {"label": "Delivery Date", "code": "delivery_date", "field_type": DT},
                            {"label": "PO Number", "code": "po_number", "field_type": T},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Procurements", "code": "total_procurements", "field_type": INT},
                            {"label": "Total Value", "code": "total_value", "field_type": DEC, "is_calculated": True, "formula": "sum(amount)"},
                            {"label": "Compliance Notes", "code": "compliance_notes", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G9",
        "title": "Asset Register Report",
        "description": "Report on organizational assets, depreciation and disposal.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Year", "code": "reporting_year", "field_type": T, "required": True},
                            {"label": "Prepared By", "code": "prepared_by", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Assets",
                "code": "assets",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Assets",
                        "code": "assets",
                        "fields": [
                            {"label": "Asset Tag", "code": "asset_tag", "field_type": T, "required": True},
                            {"label": "Description", "code": "description", "field_type": T, "required": True},
                            {"label": "Category", "code": "category", "field_type": DD, "options": ["Furniture", "Equipment", "Vehicle", "IT", "Building", "Other"], "required": True},
                            {"label": "Location", "code": "location", "field_type": T},
                            {"label": "Date Acquired", "code": "date_acquired", "field_type": DT},
                            {"label": "Acquisition Cost", "code": "acquisition_cost", "field_type": DEC, "required": True},
                            {"label": "Depreciation Rate", "code": "depreciation_rate", "field_type": PCT},
                            {"label": "Accumulated Depreciation", "code": "accumulated_depreciation", "field_type": DEC},
                            {"label": "Current Value", "code": "current_value", "field_type": DEC, "is_calculated": True, "formula": "acquisition_cost - accumulated_depreciation"},
                            {"label": "Condition", "code": "condition", "field_type": DD, "options": ["Excellent", "Good", "Fair", "Poor"]},
                            {"label": "Photo", "code": "photo", "field_type": IMG},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Assets", "code": "total_assets", "field_type": INT},
                            {"label": "Total Value", "code": "total_value", "field_type": DEC, "is_calculated": True, "formula": "sum(current_value)"},
                            {"label": "Assets Disposed", "code": "assets_disposed", "field_type": INT},
                            {"label": "New Assets Acquired", "code": "new_assets", "field_type": INT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G10",
        "title": "Inventory Report",
        "description": "Report on inventory levels, stock movements and supplies management.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Store Officer", "code": "store_officer", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Inventory Items",
                "code": "inventory-items",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Inventory Items",
                        "code": "inventory-items",
                        "fields": [
                            {"label": "Item Name", "code": "item_name", "field_type": T, "required": True},
                            {"label": "Category", "code": "category", "field_type": T},
                            {"label": "Unit", "code": "unit", "field_type": T},
                            {"label": "Opening Stock", "code": "opening_stock", "field_type": INT},
                            {"label": "Received", "code": "received", "field_type": INT},
                            {"label": "Issued", "code": "issued", "field_type": INT},
                            {"label": "Closing Stock", "code": "closing_stock", "field_type": INT, "is_calculated": True, "formula": "opening_stock + received - issued"},
                            {"label": "Minimum Level", "code": "minimum_level", "field_type": INT},
                            {"label": "Reorder Status", "code": "reorder_status", "field_type": DD, "options": ["Adequate", "Low", "Reorder Needed", "Stockout"]},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Items", "code": "total_items", "field_type": INT},
                            {"label": "Items Below Minimum", "code": "items_below_min", "field_type": INT},
                            {"label": "Inventory Value", "code": "inventory_value", "field_type": DEC},
                            {"label": "Notes", "code": "notes", "field_type": MT},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G11",
        "title": "Donor Financial Report",
        "description": "Financial report prepared for specific donors on fund utilization.",
        "reporting_frequency": "QUARTERLY",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Donor Name", "code": "donor_name", "field_type": T, "required": True},
                            {"label": "Grant Reference", "code": "grant_reference", "field_type": T, "required": True},
                            {"label": "Reporting Period", "code": "reporting_period", "field_type": T, "required": True},
                            {"label": "Project Name", "code": "project_name", "field_type": T, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Fund Utilization",
                "code": "fund-utilization",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Fund Utilization",
                        "code": "fund-utilization",
                        "fields": [
                            {"label": "Budget Line", "code": "budget_line", "field_type": T, "required": True},
                            {"label": "Approved Budget", "code": "approved_budget", "field_type": DEC},
                            {"label": "Period Expenditure", "code": "period_expenditure", "field_type": DEC, "required": True},
                            {"label": "Cumulative Expenditure", "code": "cumulative_expenditure", "field_type": DEC},
                            {"label": "Remaining Balance", "code": "remaining_balance", "field_type": DEC, "is_calculated": True, "formula": "approved_budget - cumulative_expenditure"},
                            {"label": "Utilization Rate", "code": "utilization_rate", "field_type": PCT, "is_calculated": True, "formula": "cumulative_expenditure / approved_budget * 100"},
                            {"label": "Justification", "code": "justification", "field_type": MT},
                        ],
                    }
                ],
            },
            {
                "name": "Financial Summary",
                "code": "financial-summary",
                "groups": [
                    {
                        "name": "Financial Summary",
                        "code": "financial-summary",
                        "fields": [
                            {"label": "Total Grant Amount", "code": "total_grant", "field_type": DEC},
                            {"label": "Total Utilized", "code": "total_utilized", "field_type": DEC, "is_calculated": True, "formula": "sum(cumulative_expenditure)"},
                            {"label": "Overall Utilization", "code": "overall_utilization", "field_type": PCT, "is_calculated": True, "formula": "total_utilized / total_grant * 100"},
                            {"label": "Financial Narrative", "code": "financial_narrative", "field_type": RT},
                            {"label": "Signed By", "code": "signed_by", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "code": "G12",
        "title": "Audit Report",
        "description": "Report summarizing internal or external audit findings and recommendations.",
        "reporting_frequency": "ANNUAL",
        "sections": [
            {
                "name": "Report Info",
                "code": "report-info",
                "groups": [
                    {
                        "name": "Report Info",
                        "code": "report-info",
                        "fields": [
                            {"label": "Audit Period", "code": "audit_period", "field_type": T, "required": True},
                            {"label": "Audit Type", "code": "audit_type", "field_type": DD, "options": ["Internal", "External", "Financial", "Compliance", "Operational"], "required": True},
                            {"label": "Auditor", "code": "auditor", "field_type": T, "required": True},
                            {"label": "Audit Date", "code": "audit_date", "field_type": DT, "required": True},
                        ],
                    }
                ],
            },
            {
                "name": "Findings",
                "code": "findings",
                "is_repeatable": True,
                "groups": [
                    {
                        "name": "Findings",
                        "code": "findings",
                        "fields": [
                            {"label": "Finding Reference", "code": "finding_ref", "field_type": T, "required": True},
                            {"label": "Area", "code": "area", "field_type": T, "required": True},
                            {"label": "Finding Description", "code": "finding_description", "field_type": MT, "required": True},
                            {"label": "Risk Level", "code": "risk_level", "field_type": DD, "options": ["High", "Medium", "Low"], "required": True},
                            {"label": "Recommendation", "code": "recommendation", "field_type": MT, "required": True},
                            {"label": "Management Response", "code": "management_response", "field_type": MT},
                            {"label": "Action Owner", "code": "action_owner", "field_type": T},
                            {"label": "Target Date", "code": "target_date", "field_type": DT},
                            {"label": "Status", "code": "status", "field_type": DD, "options": ["Open", "In Progress", "Closed"]},
                        ],
                    }
                ],
            },
            {
                "name": "Summary",
                "code": "summary",
                "groups": [
                    {
                        "name": "Summary",
                        "code": "summary",
                        "fields": [
                            {"label": "Total Findings", "code": "total_findings", "field_type": INT, "is_calculated": True, "formula": "count(finding)"},
                            {"label": "High Risk Findings", "code": "high_risk", "field_type": INT},
                            {"label": "Medium Risk Findings", "code": "medium_risk", "field_type": INT},
                            {"label": "Low Risk Findings", "code": "low_risk", "field_type": INT},
                            {"label": "Overall Opinion", "code": "overall_opinion", "field_type": RT},
                            {"label": "Audit Signature", "code": "audit_signature", "field_type": SIG},
                        ],
                    }
                ],
            },
        ],
    },]
