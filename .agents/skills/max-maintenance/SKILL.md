---
name: max-maintenance
description: Mantener y verificar el runtime MAX en Linux y versionar sus cambios en el repositorio original LUTS-IA.
---

Trabaja en el clon original `~/projects/LUTS-IA`. Comprueba `git remote -v` antes
de publicar; no crees un fork para actualizar esta instalación. La unidad de
usuario es `max.service`; el buscador separado es `max-searxng` en Docker.

Ejecuta `max-cli backup` antes de migrar estado. Conserva las copias fuera de Git:
incluyen la configuración privada. Para verificar cambios, usa `ruff check
max_runtime tests deploy`, `pytest -q`, `max-cli status` y una consulta
real adecuada al cambio. Distingue las pruebas simuladas de las pruebas físicas.

Mantén la memoria y el workspace MAX separados de los agentes personales de
OpenClaw. El agente de voz no necesita shell ni acceso a otros canales. Los
tokens ChatGPT los gestiona OpenClaw: no los copies, renueves en otro proceso ni
publiques. Revisa el diff y las exclusiones de secretos antes del commit.
