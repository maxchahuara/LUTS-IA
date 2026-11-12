# Validación de MAX 0.1.2

Fecha: 12 de noviembre de 2026. Repositorio original: `maxchahuara/LUTS-IA`.
Esta entrega añade HTTPS fijo con Workers y registro automático del conector en
Linux. Los resultados iniciales permanecen en el
[registro de 0.1.0 y 0.1.1](VALIDACION-2026-11-11.md).

## Entorno y verificaciones

Ubuntu 24.04, Python 3.12.3, Node 24.16.0, cloudflared 2026.10.7 y las
dependencias de `requirements.lock`. OpenClaw y su plugin Codex mantienen la
versión 2026.10.5; las sesiones y los otros agentes se conservan en su instalación.
El Worker usa compatibilidad de Cloudflare del 12 de noviembre de 2026.

| Comprobación | Resultado |
|---|---|
| Python | 57 pruebas aprobadas, incluidas validación de destinos, permisos y confirmación del registro |
| Worker JavaScript | 15 pruebas aprobadas con el runner nativo de Node; sin dependencias npm nuevas |
| Lint y unidades | Ruff correcto y unidad `max-relay.service` validada por systemd |
| TLS público | URL `workers.dev` con certificado válido y salud 200 identificando MAX 0.1.2 |
| Administración | `/v1/status` público 404; registro interno anónimo 404 |
| Firma Alexa | Petición sin firma 400; invocación real firmada del simulador de Amazon aceptada |
| Endpoint Alexa | URL fija guardada y persistida después de recargar la consola |
| Registro del conector | Identidad aleatoria solo en Linux; Worker conserva su SHA-256 y un namespace KV dedicado |
| Conectores anteriores | Detenidos y deshabilitados; URL fija comprobada con esos procesos fuera de ejecución |
| Reinicio completo | ID de arranque nuevo; MAX, edge, relay y gateway activos automáticamente, con la misma URL pública y sin arrancarlos manualmente |
| Conversación después del reinicio | Alexa encoló la consulta, Codex la completó y el simulador recuperó la respuesta final por la URL fija |
| Motor efectivo | Recibo `openai / gpt-6.1-sol / codex`, ejecución completada |
| Búsqueda y Home Assistant | SearXNG devolvió 42 resultados y la lectura autenticada de Home Assistant respondió 200 después del reinicio |
| Persistencia de contenedores | Home Assistant y SearXNG arrancaron automáticamente con `unless-stopped` |

Las pruebas del Worker comprueban conservación exacta del cuerpo firmado,
cabeceras permitidas, límites de tamaño, rechazo de destinos ajenos, ausencia
de seguimiento de redirecciones y cierre seguro cuando el origen no está listo.
El registro es idempotente y evita escrituras KV innecesarias para el mismo
origen. No se amplían las operaciones domésticas ni los permisos del agente.

## URL persistente y recuperación

La URL pública pertenece al Worker y se mantiene al reiniciar Linux o su
conector. El supervisor obtiene una nueva dirección saliente, comprueba MAX y
registra el destino usando su identidad privada. No necesita una API token
administrativa de Cloudflare ni modifica Git o el endpoint Alexa durante el
arranque. El namespace solo contiene origen y fecha; no contiene conversaciones.

La configuración instalada conserva las rutas administrativas en loopback.
Los servicios de usuario están habilitados con `Linger=yes`; MAX espera el
arranque de OpenClaw y el conector reintenta cuando faltan red o disponibilidad.
Docker y las políticas de reinicio de Home Assistant y SearXNG se conservan.

La preparación de un gateway compartido y la propagación de KV pueden alargar
la recuperación inicial. Durante ese intervalo se devuelve 503. La dirección
permanece fija y no se anuncian resultados de acciones todavía inciertos.
En este arranque en frío, la preparación del gateway compartido superó la
primera espera de MAX. systemd reintentó una vez y el runtime quedó activo a
los 293 segundos del arranque. El conector registró su nuevo destino sin cambiar
el endpoint de la skill. No se modificaron los otros agentes para esta prueba.

## Alcance

El [procedimiento reproducible](WORKERS-HTTPS.md) utiliza valores de ejemplo.
Las credenciales, identificadores y direcciones de la instalación permanecen
fuera de Git. Se conservaron copias privadas del runtime y de la identidad del
conector antes de la prueba de reinicio.

La validación de Alexa se realiza con el simulador oficial y el servicio real
de Amazon; no acredita micrófonos, altavoces ni control físico de televisores.
Los dispositivos se incorporarán en una fase posterior. Las cuotas gratuitas de
Workers/KV y la disponibilidad de la laptop e Internet siguen aplicando.
