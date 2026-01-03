# Service Boundaries

This document explains how responsibilities are split between the microservices.
It clarifies the API gateway's role as the public edge, the user service's ownership
of onboarding and identity data, the billing service's charge and invoice logic, the
avatar UI's responsibility for the user-facing agent interface plus its local AG-UI server,
its diary structuring and MiniRAG context retrieval responsibilities,
and the MiniRAG demo UI's responsibility for a static HTML/JS demo surface.
Boundaries will be updated whenever the system evolves.

