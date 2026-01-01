# Deployment Topology

This document captures the runtime deployment assumptions, such as the container
layout, service mesh (if any), ingress points, and observability infrastructure
that support the DeepAgentsSpec microservices. The avatar UI runs as a client
application (Electron/Vite) alongside its local AG-UI server, which can also be
deployed as a separate service if needed.

