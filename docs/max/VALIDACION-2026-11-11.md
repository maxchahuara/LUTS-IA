# Validación de MAX 0.1.0 y 0.1.1

Fecha: 11 de noviembre de 2026. Repositorio original: `maxchahuara/LUTS-IA`.
La implementación se instala y versiona en Linux, conservando la historia Git.

## Entorno comprobado

| Componente | Versión |
|---|---|
| Sistema de ejecución | Ubuntu 24.04, Linux x86_64 |
| Python | 3.12.3 |
| MAX | 0.1.1; base inicial 0.1.0 |
| OpenClaw / plugin Codex | 2026.10.5 / 2026.10.5 |
| Codex gestionado por el plugin | 0.160.0 |
| Modelo que respondió realmente | openai/gpt-6.1-sol |
| Home Assistant existente | 2026.5.0 |
| SearXNG | 2026.11.11-626105eec |
| Playwright CLI / Chromium | 0.1.24 / 158.0.8127.18 |
| Cloudflared | 2026.10.7 |
| pip del entorno de MAX | 26.3 |

Las dependencias Python están fijadas en `requirements.lock`. Las versiones y
digests externos comprobados están en `deploy/versions.json`. Los tokens y la
configuración real de la casa se conservan fuera de Git con permisos privados.

## Pruebas de la base 0.1.0

| Prueba | Resultado y alcance |
|---|---|
| Suite automatizada | 41 pruebas aprobadas: autenticación, aislamiento, deduplicación, cola, cancelación, recuperación, acciones, SSRF, instancia única y voz |
| Instalación desde cero | Entorno virtual independiente, instalación de lockfile y wheel, `pip check` correcto y las 41 pruebas aprobadas |
| Lint | Ruff sin errores en runtime, tests, despliegue y puente Lambda |
| Auditoría Python | 57 paquetes revisados, sin vulnerabilidades conocidas reportadas por pip-audit en esta fecha |
| Inferencia real | OpenClaw completó consultas mediante su harness Codex con la sesión ChatGPT existente; MAX no requiere API key de OpenAI |
| Búsqueda real | SearXNG devolvió resultados; el lector recuperó texto de documentación oficial y Codex generó un resumen con fuentes e informe Markdown |
| Notas | Guardado, consulta y eliminación explícita de una nota temporal |
| Reinicio real | Un trabajo en ejecución quedó interrumpido; otro en cola continuó y terminó correctamente |
| Acciones durante prueba de reinicio | Ninguna enviada; se comprobó que no se repitieran trabajos de resultado incierto |
| Continuidad HTTPS | El proceso del túnel mantuvo su PID durante el reinicio del runtime, conservando la URL de pruebas |
| Home Assistant | Autorización OAuth completada por el titular y lectura autenticada de estados |
| Entrada pública | Rutas administrativas devuelven 404; peticiones Alexa sin firma se rechazan |
| Firma Alexa | Peticiones reales de Amazon aceptadas con la verificación oficial de firma SHA-256 y timestamp |
| Modelo Alexa | Invocación «modo max» compilada para español de Estados Unidos, México y España; invocación y registro comprobados también desde el simulador de México |
| Alexa → MAX → Codex → Alexa | Invocación y consulta desde el simulador oficial; acuse inmediato, ejecución en Linux y recuperación en Alexa de la respuesta final de Codex |
| Navegador Linux | Chromium abrió el endpoint de salud mediante Playwright CLI y cerró la sesión de prueba |
| Skills del proyecto | Tres skills propias validadas: hogar, investigación y mantenimiento |

## Arranque persistente y HTTPS: 0.1.1

La suite ampliada contiene 50 pruebas aprobadas. Añade comprobaciones de salud
pública sin datos privados y de espera del arranque del gateway. Ruff y
`systemd-analyze --user verify` aprobaron las unidades instaladas.

Se sustituyó la unidad Quick Tunnel por un túnel dedicado con nombre y
credenciales persistentes, conservadas fuera del repositorio con permisos 0600.
La configuración de ingreso fue validada por `cloudflared` y el conector abrió
cuatro conexiones con Cloudflare. La publicación DNS del hostname requiere
completar la autorización de la cuenta del dominio; no se considera todavía una
URL pública verificada. El endpoint Alexa deberá actualizarse después de esa
comprobación. La [guía de despliegue](HTTPS-Y-ARRANQUE.md) utiliza valores genéricos.

Se realizaron reinicios completos de Linux y se verificó el cambio del ID de
arranque, no solo el reinicio de un servicio. `Linger=yes` permite que las
unidades arranquen sin una sesión SSH o gráfica. Docker está habilitado al inicio
y Home Assistant y SearXNG mantienen `unless-stopped`.

La primera prueba detectó que un proceso OpenClaw activo todavía no acepta
consultas durante su inicialización. La corrección espera a `/startupz` antes
de iniciar MAX. En el segundo arranque, MAX permaneció en `start-pre` mientras
el gateway se inicializaba y los tres servicios MAX quedaron activos
automáticamente a los 84 segundos, sin reinicios fallidos. La espera no depende
del estado de los canales personales. El endpoint local de salud respondió 200.
La primera consulta aceptada después de ese arranque terminó correctamente con
recibo `openai / gpt-6.1-sol / codex`; no fue necesario volver a iniciar sesión.

También se comprobó recuperación automática de los procesos MAX y cloudflared
tras terminarlos, así como resultados reales de SearXNG después de reiniciar.
Mientras se completa la autorización DNS se mantiene un enlace provisional
separado para Alexa. Se comprobó HTTPS válido, administración pública 404 y una
invocación firmada real desde el simulador de Amazon después del reinicio. Este
enlace provisional aún cambia al reiniciar su proceso; no se presenta como la
URL estable solicitada y se retirará al validar el hostname definitivo.

El simulador oficial ejercita el servicio real de Amazon y el endpoint HTTPS;
no sustituye la comprobación del micrófono, altavoz, idioma y cuenta de cada Echo.
Las pruebas domésticas automatizadas usan estados simulados de Home Assistant;
no se presentan como pruebas físicas de los electrodomésticos.

## Comprobaciones físicas pendientes

Al documentar esta entrega, el TV LG no respondió al control webOS en la dirección
previamente descubierta. El Fire Cube de la sala anunció ADB pero no completó su
conexión con Home Assistant. El LG seguía registrado por Cast y la luz existente
figuraba como no disponible. No se confirmó encendido, apagado ni volumen físicos.

Se requiere contrastar la IP actual del LG y la cuenta e idioma de cada Echo
antes de cerrar la validación de los equipos físicos.

Para probar una skill en desarrollo en los dispositivos reales, la cuenta y el
idioma deben corresponder a la skill, y debe estar habilitada para pruebas. Véase
la [guía oficial de pruebas de Amazon](https://developer.amazon.com/en-US/docs/alexa/test/test-your-skill-overview.html).

El inventario de red y los identificadores reales permanecen privados. La etiqueta
de un Echo puede registrarse por voz; es un nombre declarado por el usuario, no
una identificación automática del modelo de hardware.

## Alcance de la entrega

Funcionan el runtime local, conversación con Codex, búsqueda con fuentes, notas,
informes Markdown, cola persistente y el puente real de la skill Alexa. El control
doméstico implementa operaciones tipadas y verificación de estado, y requiere
completar las conexiones físicas anteriores antes de darlo por operativo.

La entrega 0.1.0 utilizó un Quick Tunnel. La configuración persistente 0.1.1 ya
utiliza un túnel con nombre; su publicación DNS y el cambio de endpoint Alexa
están pendientes de autorización en Cloudflare. La integración `alexa_devices`
para notificación proactiva en un Echo concreto y las ampliaciones de visión,
calendarios, documentos Office, voz local y programación aislada continúan en el
plan de incrementos. No se anuncian como capacidades ya conectadas.

La configuración, respaldos, sesiones, claves, identificadores de cuenta y
direcciones privadas se excluyen de la publicación. El workflow de GitHub ejecuta
instalación, lint y pruebas; su resultado puede consultarse en los checks del
commit o pull request correspondiente.
