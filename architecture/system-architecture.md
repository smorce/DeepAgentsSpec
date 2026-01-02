# System Architecture

This document describes the high-level components of the DeepAgentsSpec system,
the relationships between the API gateway, user service, billing service, avatar UI,
and the supporting infrastructure such as databases and messaging layers. Details are added
as the architecture evolves under the guidance of the ExecPlans.

Current high-level components:
- API Gateway: public edge for HTTP routing.
- User Service: onboarding and identity domain.
- Billing Service: invoice and billing domain.
- Avatar UI: desktop/web UI plus its AG-UI server for agent interactions.
- MiniRAG Demo UI: static HTML/JS demo UI served by a minimal HTTP server, calling the API Gateway.

