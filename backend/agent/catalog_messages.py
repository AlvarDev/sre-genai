"""User-safe catalog messages shared by the MCP client and the guardrail."""

# Returned to the agent when the catalog can't be reached or a catalog tool fails
# (catalog-mcp returns the same text); details stay in logs/traces only.
CATALOG_ERROR_MESSAGE = "Erro ao consultar o catálogo."
