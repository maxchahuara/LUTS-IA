# MAX Componentes y especificación de implementación

Fecha de investigación y de inspección local: 11 de noviembre de 2026.

Este catálogo concreta el plan inicial en componentes reutilizables, versiones candidatas y trabajo propio. La implementación del producto aún no se ha iniciado.

## Decisión de partida

El primer perfil aprovechará la instalación Linux existente: **Alexa con modo max, un adaptador MAX en Python, OpenClaw con su plugin Codex y Home Assistant**. Codex será el motor de trabajo. MAX aportará la experiencia de voz, la vinculación de personas y dispositivos, las acciones tipadas y el seguimiento de trabajos.

OpenClaw documenta un plugin que entrega sus turnos al motor real de Codex app-server. Ese plugin ya está instalado en el equipo. La siguiente prueba comprobará una ejecución del agente MAX, el motor efectivo y sus permisos. [Codex en OpenClaw](https://docs.openclaw.ai/plugins/codex-harness).

Un adaptador de motor conservará la posibilidad de una distribución autónoma mediante el SDK oficial. Ese segundo backend no es un requisito para el primer MVP. [SDK de Codex](https://learn.chatgpt.com/docs/codex-sdk).

El código propio y los componentes redistribuibles serán abiertos; Alexa y los modelos de ChatGPT serán servicios externos con sus condiciones y límites. [Alcance abierto de Codex](https://developers.openai.com/blog/codex-as-a-platform).

## Lo comprobado en Linux

La inspección por SSH utilizó la identidad conocida del host y no cambió servicios ni configuraciones.

| Elemento | Estado observado | Consecuencia |
| --- | --- | --- |
| Sistema | Ubuntu 24.04.4 LTS x86_64 | Host disponible para el MVP |
| CPU y RAM | Cuatro procesadores lógicos y 11.56 GiB | Comenzar con un trabajo pesado a la vez y medir |
| Disco | Aproximadamente 330 GiB libres | Margen para servicios y primeros datos |
| Python y Node | Python 3.12.3 y Node 24.16.0 | Mantener un entorno independiente para MAX |
| OpenClaw | 2026.10.5, gateway activo | Reutilizar con un agente y ámbito propios |
| Plugin Codex | 2026.10.5, habilitado, Codex administrado 0.160.0 | La integración no depende del CLI global |
| CLI global | Codex 0.146.0 | Es un runtime separado |
| Home Assistant | Contenedor activo 2026.5.0 | Aprovechar la instancia existente |
| Dispositivos registrados | LG mediante Cast y una luz WiZ | Falta vincular webOS para el control completo del LG |
| Componentes incluidos | Alexa Devices, MCP, webOS y ADB | Están disponibles, pero no aparecen vinculados como entradas |

OpenClaw tiene un perfil OAuth de OpenAI configurado. El estado del CLI global indica una sesión distinta sin iniciar; eso no determina la vigencia de la autorización de OpenClaw. Todavía falta comprobar inferencia, modelo y renovación en el perfil que utilizará MAX.

La instancia Linux es distinta del entorno Windows/WSL del proyecto de lavadora. Las IP, usuarios, nombres personales y rutas particulares se conservan en el inventario privado fuera de Git.

## Versiones y compatibilidad

| Componente | Instalado | Publicación consultada | Tratamiento |
| --- | --- | --- | --- |
| OpenClaw | 2026.10.5 | 2026.11.3 | Probar la instalación actual antes de actualizar |
| Plugin Codex | 2026.10.5 con Codex 0.160.0 | 2026.11.3 con Codex 0.164.0 | Mantener compatible el par host/plugin |
| Codex independiente | 0.146.0 | 0.167.1 | No es obligatorio sustituirlo para usar el runtime administrado |
| Home Assistant | 2026.5.0 | 2026.11.1 | Evaluar actualización del contenedor según las funciones necesarias |
| Biblioteca MCP de HA | 1.26.0 | La versión actual de HA utiliza 2.3.0 | Separar dependencias y probar negociación de protocolo |

Fuentes de publicaciones: [OpenClaw](https://www.npmjs.com/package/openclaw), [plugin Codex](https://www.npmjs.com/package/@openclaw/codex), [Codex](https://www.npmjs.com/package/@openai/codex), [Home Assistant](https://pypi.org/project/homeassistant/).

El plugin nuevo declara compatibilidad con la API de OpenClaw 2026.11.3. No debe instalarse aislado sobre el host 2026.10.5 sin comprobar su compatibilidad. El par instalado coincide en versión.

La opción de solo lectura y otros cambios del servidor MCP de Home Assistant llegaron en noviembre. No se supondrá que la instalación de mayo ofrece todas las opciones de la documentación nueva. [Changelog 2026.11](https://www.home-assistant.io/changelogs/core-2026.11/).

Home Assistant actual declara Python 3.14.2 en sus metadatos. El contenedor incorpora su propio Python: MAX puede conservar Python 3.12 en el host. Las versiones publicadas de las tablas son candidatas observadas, no un conjunto instalado o probado.

## Arquitectura del primer perfil

~~~mermaid
flowchart TD
  A[Echo y Fire TV] --> B[Skill modo max]
  B --> C[Entrada HTTPS validada]
  C --> D[MAX Voz e identidades]
  D --> E[Acciones domésticas rápidas]
  D --> F[Trabajos y resultados persistentes]
  E --> H[Home Assistant]
  F --> G[Agente MAX en OpenClaw]
  G --> I[Codex administrado]
  G --> J[Herramientas y skills permitidas]
  J --> H
  J --> K[Búsqueda y archivos]
  H --> L[LG y luz WiZ]
  H --> M[Solicitudes y anuncios de Alexa]
  F --> N[Consulta por voz y panel local]
~~~

El adaptador de entrada admitirá un Lambda pequeño o un web service directo con ASK SDK, firma y timestamp. La elección se resolverá con la skill actual y el despliegue más sencillo. [Web services Python](https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit-sdk-for-python/host-web-service.html).

El presupuesto interno será menor que el plazo de unos ocho segundos de Alexa. Las peticiones largas continuarán como trabajos consultables; una respuesta progresiva no amplía ese plazo. [Plazo de Alexa](https://developer.amazon.com/en-US/docs/alexa/custom-skills/send-the-user-a-progressive-response.html).

El endpoint público terminará en el adaptador limitado de MAX. El API OpenResponses de OpenClaw se documenta como acceso de operador completo; el gateway y los protocolos de administración permanecerán locales. [Alcance del API](https://docs.openclaw.ai/gateway/openresponses-http-api).

Se propondrá un agente MAX con workspace y herramientas específicos. Si la versión instalada no permite el aislamiento requerido, se utilizará un proceso separado. El ámbito doméstico no recibirá por defecto las capacidades del workspace personal actual.

## Puentes Alexa revisados

| Proyecto | Evidencia | Uso propuesto |
| --- | --- | --- |
| [nicknmorty/openclaw-alexa-bridge](https://github.com/nicknmorty/openclaw-alexa-bridge) | MIT; helpers Python, pruebas, validación de skill ID y timeout HTTP acotado | Referencia inicial de puente y empaquetado |
| [Cormazabal/openclaw-alexa-voice](https://github.com/Cormazabal/openclaw-alexa-voice) | MIT; proxy, Lambda y entrega diferida mediante HA | Referencia de captura y respuesta diferida |
| [SufiSR/AlexaClaw](https://github.com/SufiSR/AlexaClaw) | GPL 3.0 en metadatos | Comparación funcional; una incorporación requeriría estrategia de licencia compatible |
| [SufiSR/AlexaClaw-Client](https://github.com/SufiSR/AlexaClaw-Client) | Sin licencia en la raíz consultada; varios archivos de ejecución vacíos | Documentación de referencia, sin incorporar su código como base |
| [Hermes con Codex](https://hermes-agent.nousresearch.com/docs/user-guide/features/codex-app-server-runtime) | Runtime Codex opcional con cobertura de herramientas distinta | Alternativa evaluada; no requiere añadir otro gateway al host |

La revisión estática encontró ajustes concretos para MAX:

- El proxy de Cormazabal utiliza nombres de sesión compartidos y last_called para dirigir TTS. MAX conservará el dispositivo de origen y un ámbito por hogar, usuario y conversación.
- Su Lambda configura diez segundos de timeout de red. MAX aplicará un plazo global inferior al presupuesto de Alexa, incluyendo reintentos.
- El puente de nicknmorty comprueba la skill y acota el HTTP; necesita la capa propia de identidad, persistencia y asociación de dispositivos.
- La ruta solicitada para MAX utilizará Codex y la autorización ChatGPT correspondiente; no copiará una dependencia de otro proveedor de IA.

Archivos revisados: [proxy.js](https://github.com/Cormazabal/openclaw-alexa-voice/blob/main/proxy.js), [su Lambda](https://github.com/Cormazabal/openclaw-alexa-voice/blob/main/lambda/lambda_function.py), [helpers Python](https://github.com/nicknmorty/openclaw-alexa-bridge/blob/main/lambda/alexa_bridge.py), [Lambda del puente](https://github.com/nicknmorty/openclaw-alexa-bridge/blob/main/lambda/lambda_function.py). No se han probado estos proyectos en la casa.

La reutilización de fragmentos con sus avisos no exige convertir LUTS-IA en un fork. El código del producto y su historial seguirán en el repositorio original.

## Autenticación y credenciales

En el perfil inicial, OpenClaw conservará la propiedad de su autorización y renovación. MAX no copiará sus tokens ni ejecutará otro renovador sobre la misma sesión. El panel identificará el motor y la cuenta conectada.

Una distribución autónoma implementará su registro SiWC propio. El DevKit tiene licencia no comercial, por lo que la propuesta utiliza el protocolo documentado y bibliotecas apropiadas para el objetivo de distribución. [Flujo oficial](https://developers.openai.com/siwc/token-sharing-open-source/sign-in), [licencia del DevKit](https://github.com/openai/sign-in-with-chatgpt-devkit/blob/main/LICENSE).

El callback de loopback llega a la computadora donde está el navegador. Una incorporación desde Windows a un servicio Linux debe resolverlo mediante un procedimiento local o transporte SSH probado. [Hosts propios remotos](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms).

El vínculo Alexa a MAX utilizará credenciales del hogar MAX, independientes del permiso de inferencia. Se separarán registros de cuenta y workspace, incluso cuando tengan el mismo email. [Gestión de cuentas SiWC](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions).

El almacén de secretos deberá funcionar con el servicio Linux sin depender de una sesión gráfica desbloqueada. Los secretos no entrarán en prompts, resultados de herramientas ni registros públicos.

La ruta SiWC tiene restricciones específicas. Entre ellas están los parámetros y herramientas admitidos y la necesidad de completar el stream. La ejecución local de herramientas no equivale a habilitar herramientas alojadas no admitidas. La carga de herramientas diferidas de OpenClaw se comprobará contra esa ruta; su configuración directa es una candidata cuando la búsqueda de herramientas no sea compatible. [Límites SiWC](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations), [carga de herramientas de OpenClaw](https://docs.openclaw.ai/plugins/codex-harness-reference).

## Integraciones domésticas

| Integración | Trabajo |
| --- | --- |
| webOS | Vincular el LG y probar volumen, entradas, aplicaciones y encendido |
| Alexa Devices | Vincular cuenta con MFA y asociar cada Echo/Fire TV a su habitación |
| MCP Server | Seleccionar las herramientas y entidades necesarias |
| WiZ | Utilizar la luz ya configurada para la primera escena |
| ADB de Fire TV | Añadir únicamente para funciones que no cubra la vía Alexa |

La instalación actual contiene send_text_command, send_sound y send_info_skill. Sus efectos y destinos deben probarse con la cuenta vinculada. [Alexa Devices](https://www.home-assistant.io/integrations/alexa_devices/), [comando de texto](https://www.home-assistant.io/actions/alexa_devices.send_text_command/).

El LG registrado por Cast no acredita una vinculación webOS completa. El encendido desde apagado se comprobará por la vía compatible del modelo, como Wake-on-LAN o HDMI-CEC. [webOS](https://www.home-assistant.io/integrations/webostv/).

MCP ofrecerá herramientas al agente. Un cliente REST/WebSocket podrá ejecutar acciones rápidas y observar estados sobre las entidades permitidas. [REST](https://contributors.home-assistant.io/core/internals/rest-api/), [WebSocket](https://contributors.home-assistant.io/core/internals/websocket-api/).

Se mantendrán las bibliotecas aiowebostv y aioamazondevices bajo gestión del contenedor. No hace falta otra sesión directa sobre cada equipo para el primer MVP.

## Web y navegador

Habrá una interfaz de búsqueda con un adaptador de búsqueda disponible para la cuenta/modelo y otro para SearXNG propio. El JSON de SearXNG debe habilitarse; muchas instancias públicas no lo ofrecen. [API de búsqueda](https://docs.searxng.org/dev/search_api.html).

Trafilatura extraerá texto y metadatos. Cada resultado guardará sus URL, título, fecha y evidencia. Habrá versión breve para voz y detallada para pantalla. La lectura web limitará tamaño, tiempo y destinos; no convertirá enlaces externos en acceso a servicios privados de la LAN.

Para Codex se prioriza Playwright CLI con su skill; MCP queda como alternativa para flujos que necesiten esa interfaz. Microsoft documenta ambos usos. [CLI](https://github.com/microsoft/playwright-cli), [MCP](https://github.com/microsoft/playwright-mcp).

Los trabajos de proyectos tendrán workspace e identidad de GitHub propios. El MCP oficial de GitHub admite selección de herramientas y modo de solo lectura. [GitHub MCP Server](https://github.com/github/github-mcp-server).

## Trabajos y memoria

Se propone **Huey con SQLite** para la cola y **aiosqlite** para el estado de MAX. Huey ofrece trabajo programado y resultados con almacenamiento SQLite, sin un servidor de colas adicional en este host. [Guía](https://huey.readthedocs.io/en/latest/guide.html), [licencia y proyecto](https://github.com/coleifer/huey).

MAX necesitará sus registros de identidad, progreso, destinatario y evidencia. La cola por sí sola no evita que se repita una acción externa después de una caída.

Los estados serán en cola, ejecutando, esperando información, esperando autorización, completado, fallido y cancelado. La cancelación se propagará al motor; los efectos ya ejecutados se informarán. Después de un timeout se comprobará el estado antes de repetir una orden.

La memoria empezará con preferencias explícitas y búsqueda por texto, con propietario, origen, fecha y borrado. La memoria del agente MAX se mantendrá separada del workspace personal actual. No se necesita una base vectorial para el primer MVP.

## Bibliotecas y versiones candidatas

Versiones consultadas en PyPI. Los requisitos de Python y licencias son metadatos publicados, complementados con los archivos de repositorio cuando faltaban. La tabla no es un conjunto resuelto ni probado.

| Paquete y fuente primaria | Versión observada | Python declarado | Licencia indicada | Función |
| --- | --- | --- | --- | --- |
| [fastapi](https://pypi.org/project/fastapi/) | 0.162.4 | >=3.10 | MIT | API de MAX |
| [uvicorn](https://pypi.org/project/uvicorn/) | 0.54.0 | >=3.10 | BSD-3-Clause | Servidor HTTP |
| [httpx](https://pypi.org/project/httpx/) | 0.28.1 | >=3.8 | BSD-3-Clause | Clientes HTTP y streams |
| [pydantic](https://pypi.org/project/pydantic/) | 2.14.3 | >=3.10 | MIT | Validación de contratos |
| [pydantic-settings](https://pypi.org/project/pydantic-settings/) | 2.16.2 | >=3.11 | MIT | Configuración tipada |
| [Authlib](https://pypi.org/project/Authlib/) | 1.9.5 | >=3.10 | BSD-3-Clause | OAuth del perfil autónomo |
| [cryptography](https://pypi.org/project/cryptography/) | 50.0.2 | !=3.9.0,!=3.9.1,>=3.9 | Apache-2.0 OR BSD-3-Clause | Protección criptográfica |
| [keyring](https://pypi.org/project/keyring/) | 25.7.0 | >=3.9 | MIT | Almacén del sistema; validar modo headless |
| [mcp](https://pypi.org/project/mcp/) | 2.3.0 | >=3.10 | MIT | Herramientas interoperables |
| [openai-codex](https://pypi.org/project/openai-codex/) | 0.167.1 | >=3.10 | Apache-2.0 | Backend Codex autónomo opcional |
| [ask-sdk-core](https://pypi.org/project/ask-sdk-core/) | 1.19.0 | >2.6, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.* | Apache 2.0 | Solicitudes y respuestas de Alexa |
| [ask-sdk-webservice-support](https://pypi.org/project/ask-sdk-webservice-support/) | 1.3.3 | >2.6, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.* | Apache 2.0 | Verificación de entrada HTTPS |
| [aiosqlite](https://pypi.org/project/aiosqlite/) | 0.22.1 | >=3.9 | MIT | Estado y trabajos de MAX |
| [SQLAlchemy](https://pypi.org/project/SQLAlchemy/) | 2.1.8 | >=3.11 | MIT | ORM opcional |
| [alembic](https://pypi.org/project/alembic/) | 1.20.1 | >=3.10 | MIT | Migraciones opcionales |
| [APScheduler](https://pypi.org/project/APScheduler/) | 3.11.3 | >=3.8 | MIT | Alternativa de scheduler; evitar duplicarlo |
| [tenacity](https://pypi.org/project/tenacity/) | 9.2.1 | >=3.10 | Apache-2.0 | Reintentos adecuados |
| [structlog](https://pypi.org/project/structlog/) | 26.1.0 | >=3.10 | MIT OR Apache-2.0 | Registros estructurados |
| [prometheus-client](https://pypi.org/project/prometheus-client/) | 0.26.0 | >=3.9 | Apache-2.0 AND BSD-2-Clause | Métricas opcionales |
| [pytest](https://pypi.org/project/pytest/) | 9.2.0 | >=3.10 | MIT | Pruebas |
| [pytest-asyncio](https://pypi.org/project/pytest-asyncio/) | 1.4.1.post1 | >=3.10 | Apache-2.0 | Pruebas asíncronas |
| [respx](https://pypi.org/project/respx/) | 0.23.1 | >=3.8 | BSD-3-Clause | Dobles HTTP |
| [ruff](https://pypi.org/project/ruff/) | 0.17.4 | >=3.7 | MIT | Formato y análisis |
| [pip-audit](https://pypi.org/project/pip-audit/) | 2.10.1 | >=3.10 | Apache-2.0 | Auditoría de dependencias |
| [trafilatura](https://pypi.org/project/trafilatura/) | 2.3.1 | >=3.10 | Apache-2.0 | Lectura web |
| [zeroconf](https://pypi.org/project/zeroconf/) | 0.154.0 | >=3.11 | LGPL-2.1-or-later | Descubrimiento opcional |
| [async-upnp-client](https://pypi.org/project/async-upnp-client/) | 0.49.0 | >=3.11 | Apache-2.0 | Descubrimiento SSDP opcional |
| [aiowebostv](https://pypi.org/project/aiowebostv/) | 1.0.2 | >=3.12 | Apache-2.0 | Control LG; preferir gestión por HA |
| [androidtv](https://pypi.org/project/androidtv/) | 0.0.75 | No declarado | MIT | Control ADB; preferir integración HA |
| [homeassistant](https://pypi.org/project/homeassistant/) | 2026.11.1 | >=3.14.2 | Apache-2.0 | Contenedor independiente |
| [huey](https://pypi.org/project/huey/) | 3.5.4 | Probar en Python 3.12 | MIT | Cola SQLite propuesta |

No se instalarán todas las filas. ORM, schedulers, métricas y diagnóstico son alternativas o ampliaciones. El perfil OpenClaw reutiliza su Codex administrado; openai-codex corresponde al backend autónomo. Las versiones finales se resolverán con sus dependencias transitivas y hashes en un entorno limpio.

Para documentos se podrán incorporar [pypdf](https://pypi.org/project/pypdf/), [ReportLab](https://pypi.org/project/reportlab/), [python-docx](https://github.com/python-openxml/python-docx), [openpyxl](https://openpyxl.readthedocs.io/) y [python-pptx](https://github.com/scanny/python-pptx). Sus salidas necesitarán render o recálculo según el formato. Estas herramientas locales no suponen acceso a herramientas alojadas por el mero inicio de sesión con ChatGPT.

## Skills revisadas

| Skill | Aplicación y requisitos |
| --- | --- |
| [Playwright CLI de Microsoft](https://github.com/microsoft/playwright-cli/tree/main/skills/playwright-cli) | Navegador, capturas y pruebas; Node y navegador |
| [Playwright de OpenAI](https://github.com/openai/skills/tree/main/skills/.curated/playwright) | Flujo CLI de navegador; Apache 2.0 consultada |
| [PDF de OpenAI](https://github.com/openai/skills/tree/main/skills/.curated/pdf) | Extracción, generación y render; Apache 2.0 consultada |
| [GitHub CI de OpenAI](https://github.com/openai/skills/tree/main/skills/.curated/gh-fix-ci) | Diagnóstico de checks; gh y autorización; Apache 2.0 consultada |
| [Revisión de seguridad](https://github.com/openai/skills/tree/main/skills/.curated/security-best-practices) | Referencia de revisión del stack; verificar sus recursos y licencia antes de distribuir |
| [Agent Skills](https://agentskills.io/specification) | Formato abierto de los módulos propios |

Son referencias estudiadas, no skills instaladas o ejecutadas en Linux. Cada incorporación registrará versión, licencia, herramientas y requisitos.

Skills propias: max-home, max-research, max-projects, max-documents, max-memory, max-routines y max-diagnostics. Cada procedimiento se construirá sobre herramientas funcionales y describirá cómo comprobar su resultado.

## Voz local posterior

| Proyecto | Función | Consideración |
| --- | --- | --- |
| [Linux Voice Assistant](https://github.com/OHF-Voice/linux-voice-assistant) | Satélite para Assist mediante ESPHome | Apache 2.0; experimental |
| [Wyoming](https://github.com/OHF-Voice/wyoming) | Comunicación entre servicios de voz | MIT |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Transcripción local | MIT; medir modelo y CPU |
| [Piper](https://github.com/OHF-Voice/piper1-gpl) | Síntesis local | GPL 3.0; revisar además cada voz |
| [micro-wake-word](https://github.com/OHF-Voice/micro-wake-word) | Entrenamiento de activación | Apache 2.0; necesita modelo adecuado |
| [openWakeWord](https://github.com/dscripka/openWakeWord) | Activación por palabra | Código Apache 2.0; modelos incluidos no comerciales |

Linux Voice Assistant puede servir para una activación directa de MAX en un cliente propio. El proyecto se declara experimental y exige audio y pruebas acústicas. [Descripción](https://github.com/OHF-Voice/linux-voice-assistant/blob/main/README.md).

openWakeWord declara soporte actual principalmente en inglés y modelos preentrenados con licencia no comercial. No se distribuirán como modelos sin restricciones para español. Se debe evaluar o entrenar un modelo con datos y licencias apropiados. [Soporte y licencias](https://github.com/dscripka/openWakeWord/blob/main/README.md).

El canal inicial seguirá utilizando el reconocimiento y la voz de Alexa. Una voz propia será un cliente o satélite separado, sin modificar el firmware de los Echo.

## Contratos de MAX que faltan implementar

La solicitud normalizada contendrá hogar, usuario, dispositivo, sesión, requestId, locale, texto y permisos. El registro mapeará identificadores de Alexa a destinos concretos de Home Assistant.

Rutas propuestas, aún no implementadas:

| Ruta | Responsabilidad |
| --- | --- |
| POST /v1/alexa/events | Recibir evento validado |
| GET /v1/setup/status | Mostrar conexiones y requisitos pendientes |
| GET /v1/devices | Inventario permitido |
| GET /v1/capabilities | Funciones instaladas |
| GET /v1/jobs/{id} | Estado y resultado autorizado |
| POST /v1/jobs/{id}/cancel | Cancelación |
| POST /v1/authorizations/{id}/decision | Revisión desde sesión autenticada |
| GET /v1/results/{id} | Resultado completo y fuentes |

Cada herramienta declarará esquema de entrada, ámbito, efectos, plazo, repetición y evidencia de salida. Las primeras serán lectura de estado, encendido/apagado, volumen, solicitud de Alexa, búsqueda, lectura de página, estado/cancelación y memoria explícita.

El formateador escapará SSML, limitará la longitud y separará texto hablado de visuales. Los errores técnicos no se leerán como si fueran respuestas del asistente.

## Backlog técnico

| Unidad | Entregable | Aceptación |
| --- | --- | --- |
| MAX 01 | Configuración y diagnóstico | Detecta dependencias sin mostrar secretos |
| MAX 02 | Registro de hogares y equipos | Usuario y destino correctos |
| MAX 03 | Adaptador de Alexa | Origen validado, captura, ayuda y salida |
| MAX 04 | Voz y visuales | SSML válido y contenido acotado |
| MAX 05 | Enrutador rápido | Controles dentro del presupuesto de voz |
| MAX 06 | Broker de permisos | Ejecuta solo capacidades y argumentos permitidos |
| MAX 07 | Adaptador de motor | Comprueba Codex, progreso, finalización y cancelación |
| MAX 08 | Cola y recuperación | Conserva trabajos y deduplica los casos probados |
| MAX 09 | Home Assistant | Ejecuta y observa estado real |
| MAX 10 | Entrega mediante Alexa | Destino y avisos correctos |
| MAX 11 | Investigación web | Resumen con fuentes y evidencia |
| MAX 12 | Panel local | Conexiones, resultados y permisos visibles |
| MAX 13 | Skills propias | Procedimientos sobre herramientas verificadas |
| MAX 14 | Operación y copias | Reinicio y restauración de prueba |
| MAX 15 | Publicación abierta | Instalación reproducible, licencias, CI y releases |

El MVP probará dos dispositivos y dos perfiles, solicitudes duplicadas y una tarea que tarde más de ocho segundos. Enviar una orden no acreditará su efecto físico sin evidencia.

## Operación y distribución

MAX y su worker tendrán un entorno y directorio de datos propios. La primera distribución puede utilizar systemd y el contenedor HA existente. SearXNG y navegador se incorporarán como servicios opcionales según la carga.

Cada servicio mostrará salud, versión y último error. Se propone [restic](https://github.com/restic/restic) para copias cifradas y verificables, junto con el respaldo de HA. SQLite se copiará mediante un procedimiento consistente, no copiando a ciegas una base activa.

La actualización de HA y del par OpenClaw/plugin tendrá respaldo y restauración probada. La etiqueta stable del contenedor se sustituirá por una versión o digest registrado al preparar el despliegue.

origin y el historial permanecerán en el repositorio original. Los paquetes importados conservarán sus avisos; un repositorio público sin licencia no se tratará como permiso general de reutilización. Credenciales, conversaciones y datos reales de red quedarán fuera de Git.

La publicación incluirá incorporación sin secretos compartidos, configuración de ejemplo, matriz de equipos/idiomas, política de datos, herramientas habilitables y desinstalación. Cada conector externo tendrá su autorización correspondiente.

## Orden de implementación

1. Registrar el estado actual y completar inventario Alexa.
2. Preparar un agente MAX aislado y comprobar un turno real con Codex.
3. Vincular webOS y Alexa Devices y verificar controles en HA.
4. Implementar modo max, identificación de sesión y entrada segura.
5. Añadir controles rápidos y medir tiempos.
6. Incorporar trabajos persistentes y recuperación.
7. Añadir búsqueda, fuentes y entrega diferida.
8. Probar el MVP en los equipos.
9. Incorporar documentos, proyectos, memoria y conectores.
10. Preparar distribución pública y, posteriormente, voz propia o Alexa+.

La investigación deja identificadas las piezas y los contratos. La autorización de cuentas, el reconocimiento en los equipos y los efectos físicos requieren sus pruebas de integración.
