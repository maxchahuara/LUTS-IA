# MAX Alexa Investigación técnica y plan de acción

Fecha de consulta: 11 de noviembre de 2026. Repositorio: maxchahuara/LUTS-IA.

La inspección posterior de la laptop y el catálogo de implementación concretan esta propuesta en [Componentes y especificación de MAX](COMPONENTES-Y-ESPECIFICACION.md). Ese catálogo incorpora las versiones realmente instaladas y la ruta inicial de reutilización de OpenClaw con su motor Codex.

## Propuesta y resultado esperado

MAX será un asistente ampliable que recibe solicitudes desde Alexa, ejecuta acciones en la casa y trabaja con Codex en una laptop Linux de la misma red. El desarrollo continuará en el repositorio original, conservando su historial. Esta propuesta prepara la implementación; las capacidades descritas como futuras requieren sus respectivas pruebas.

La combinación recomendada es:

1. Una skill personalizada con la invocación **modo max**.
2. Un servicio MAX en Linux para sesiones, permisos, herramientas y trabajos.
3. Codex como motor de trabajo; la primera integración aprovechará OpenClaw y su plugin Codex ya disponibles. Un adaptador independiente conservará la opción de SDK/app-server directo.
4. Inicio de sesión oficial con ChatGPT y autorización para usar el plan del usuario.
5. Home Assistant para dispositivos, estados, escenas y la integración con Alexa.
6. Herramientas MCP y skills propias para ampliar capacidades por módulos.

El primer resultado demostrable debe permitir abrir modo max, conversar, encender el LG, utilizar una función de Alexa y solicitar una búsqueda con un resumen respaldado por fuentes. Una petición larga debe continuar como trabajo consultable y cancelable.

La ampliación puede ser grande; la capacidad efectiva dependerá de las herramientas instaladas, los permisos concedidos, la disponibilidad de los servicios y los límites del plan.

## Situación del proyecto y del entorno

La versión actual contiene el modelo de interacción y un backend Python para Alexa. Usa una llamada heredada a OpenAI, una identidad de asistente médico, un historial global y una clave de ejemplo dentro del código. No contiene un motor de acciones, almacenamiento de sesiones aisladas ni una cola de trabajos. La revisión sintáctica de Python y JSON fue satisfactoria.

La laptop Linux ya fue inspeccionada por SSH con comprobación de su identidad conocida. Ejecuta Ubuntu 24.04.4 LTS x86_64, tiene cuatro procesadores lógicos, 11.56 GiB de RAM y aproximadamente 330 GiB libres en el volumen consultado. Están disponibles Python 3.12.3, Node 24.16.0, Docker, OpenClaw 2026.10.5 y Home Assistant 2026.5.0. El plugin Codex de OpenClaw administra un runtime 0.160.0; es independiente del CLI global 0.146.0. La GPU no es un requisito propuesto para el MVP, que utilizará inferencia en la nube.

El descubrimiento local identificó un LG OLED55C4PSA, dos Fire TV de la familia declarada por el propietario como Cube y un equipo que devuelve Echo_Show_5 en su autodescripción local. La Echo Dot mencionada por el propietario sigue pendiente de asociación. Las direcciones, nombres personales y evidencias de red se guardan en el inventario privado local, fuera de los archivos que se publicarán en Git.

La instalación Linux de Home Assistant está activa y tiene registrados el LG mediante Google Cast y una luz WiZ. Los componentes webOS, Alexa Devices y MCP están incluidos en esa instalación, pero sus entradas de configuración todavía no aparecen vinculadas. Es un entorno distinto de la instalación Windows/WSL informada por el conector de lavadora de otro proyecto; ese conector podrá integrarse después de comprobar su servicio actual.

## Lo que permiten las plataformas

### Inicio de sesión con ChatGPT

La documentación oficial ofrece un flujo para aplicaciones open source y alojadas por el usuario. Distingue la identificación de la persona del permiso para consumir su plan. Este flujo no entrega las conversaciones ni todo el contexto de su cuenta de ChatGPT. El servidor local necesita una identidad de host persistente. [Descripción oficial](https://developers.openai.com/siwc/token-sharing-open-source).

El registro inicial utiliza OAuth con PKCE, state y nonce. El callback local devuelve un client_id emitido que debe conservarse para esa cuenta y workspace. La aplicación valida el ID token y los permisos realmente concedidos. Debe solicitarse y comprobarse chatgpt.tokens.use.direct. [Registro e inicio de sesión](https://developers.openai.com/siwc/token-sharing-open-source/sign-in).

Los modelos deben consultarse para la cuenta conectada y verificarse mediante una inferencia completada. La integración usará el endpoint público Responses y procesará el flujo hasta su evento final. Se enviará store=false y stream=true. Una lista de modelos de app-server puede estar almacenada o incluida en el cliente y no demuestra acceso efectivo. [Modelos e inferencia](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference).

La ruta está sujeta a limitaciones de preview. Permite herramientas function/custom y ejecución local mediante Codex. Web search depende del modelo y de la política de cuenta. Actualmente no incluye los conectores MCP alojados de Responses, file search, Code Interpreter, computer use nativo, generación de imágenes ni transcripción/audio por esa autorización. Las herramientas locales propias son otra capa. Tampoco admite varios parámetros de la API general, como background, temperature o max_output_tokens; la integración tendrá que ajustarse a esta ruta concreta. [Limitaciones actuales](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations).

Decisión: cada instalación utilizará una cuenta y permisos autorizados. En el primer perfil, OpenClaw conservará la propiedad de su autorización y renovación; la distribución autónoma de MAX tendrá un registro SiWC propio. El modelo no se fijará por suposición a un nombre comercial nuevo. El selector presentará los modelos permitidos y el perfil de voz priorizará latencia; los trabajos largos podrán elegir más razonamiento.

### Codex como motor

La configuración oficial de SiWC permite suministrar el token propio de MAX al proceso hijo de app-server. La aplicación debe gestionar su renovación y reiniciar/reanudar el proceso cuando corresponda. El protocolo permite iniciar y reanudar chats y observar el estado terminal del turno. [Codex con ChatGPT plan](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server).

Existen SDK oficiales para TypeScript y Python. La documentación describe el SDK Python como estable, con un runtime fijado por su distribución. El servicio MAX utilizará Python; el primer adaptador aprovechará OpenClaw y su plugin Codex existente. El SDK queda como opción para el backend autónomo, antes de introducir un cliente RPC propio. [SDK de Codex](https://learn.chatgpt.com/docs/codex-sdk).

Hay interfaces experimentales en app-server, incluido el transporte WebSocket y herramientas dinámicas. La documentación de migración también advierte que app-server es experimental para producción. Debe aislarse detrás de un adaptador y fijar una versión probada. El antiguo codex mcp-server fue retirado: MAX no basará su arquitectura en él. [App-server](https://learn.chatgpt.com/docs/app-server), [migración del antiguo servidor MCP](https://learn.chatgpt.com/docs/mcp-server).

Propuesta de adaptación: una interfaz de motor permitirá conservar la voz, los trabajos y las herramientas si cambia el SDK. Una implementación directa de Responses con herramientas locales podría ser alternativa técnica para determinados flujos; no se activará como sustitución silenciosa del motor solicitado.

### Invocación y lenguaje de Alexa

La skill se configurará como modo max, en minúsculas en su modelo. El inicio previsto será **Alexa, abre modo max**. Una vez abierta, el asistente se presentará como Max. La publicación y el reconocimiento del nombre deben validarse en la consola y en los dispositivos reales. [Reglas de invocación](https://www.developer.amazon.com/en-US/docs/alexa/custom-skills/choose-the-invocation-name-for-a-custom-skill.html).

El nombre de una skill y la palabra que despierta un Echo son mecanismos distintos. Amazon documenta las palabras de activación disponibles para sus equipos. Un futuro acceso que se active únicamente con Max se plantearía mediante un dispositivo o cliente de voz propio, con pruebas de su reconocimiento. [Funcionamiento de voz de Echo](https://digprjsurvey.amazon.com/csad/help/node/201602230).

Para consultas abiertas se sustituirá el uso de AMAZON.Person por un diseño con AMAZON.SearchQuery, disponible en es-MX, es-ES y es-US. Amazon exige frases portadoras en las expresiones de ejemplo de un intent; no basta con cambiar el tipo y conservar solo {query}. Probaremos expresiones como Max consulta, Max busca y Max haz, más intents específicos de control. [Tipos y requisitos de SearchQuery](https://developer.amazon.com/en-US/docs/alexa/custom-skills/slot-type-reference.html).

### Tiempo disponible para responder

Una skill clásica dispone de aproximadamente ocho segundos para devolver la respuesta completa. Las respuestas progresivas permiten informar que está trabajando, pero no amplían ese plazo. [Respuestas progresivas](https://developer.amazon.com/en-US/docs/alexa/custom-skills/send-the-user-a-progressive-response.html).

Consecuencia de diseño: separar las acciones rápidas de las tareas que pueden tardar. El servicio mantendrá un plazo interno inferior al de Alexa. Si el resultado no está listo, devolverá un identificador de trabajo o una confirmación breve y continuará en segundo plano.

### Acciones de casa y funciones de Alexa

Una skill personalizada recibe sus propias solicitudes. Los modelos Smart Home describen dispositivos y capacidades implementadas por la integración; combinar modelos no equivale a recibir acceso general a todos los dispositivos o skills de la cuenta. [Modelos de Alexa Smart Home](https://developer.amazon.com/en-US/alexa/alexa-skills-kit/get-deeper/smart-home-skills).

Home Assistant ofrece un servidor MCP para consultar y controlar la casa. Actualmente distingue herramientas limitadas a las entidades expuestas a Assist de un conjunto administrativo con acceso mucho más amplio. El MVP seleccionará explícitamente el conjunto de control de dispositivos y las entidades permitidas. [Servidor MCP de Home Assistant](https://www.home-assistant.io/integrations/mcp_server/).

La integración incluida Alexa Devices descubre equipos de la cuenta Amazon, requiere MFA mediante aplicación autenticadora y ofrece anuncios y acciones sobre dispositivos. Es una integración de Home Assistant con dependencia de la nube de Amazon; no debe presentarse como un API público de Amazon para desarrolladores. [Alexa Devices](https://www.home-assistant.io/integrations/alexa_devices/).

Su acción send_text_command envía una solicitud como si hubiera sido pronunciada al dispositivo. Ofrece una vía para funciones nativas, dispositivos enlazados y reproducción, pendiente de probar en la cuenta, idioma y equipos reales. MAX diferenciará comando enviado de acción confirmada: el envío por sí solo no acredita el estado final. [Acción documentada](https://www.home-assistant.io/actions/alexa_devices.send_text_command/).

El control local del LG será preferente. Home Assistant soporta webOS, volumen, fuentes, reproducción y notificaciones. El encendido puede necesitar una automatización con Wake-on-LAN o HDMI-CEC y configuración del TV; se probará específicamente desde apagado y con su conexión real. [Integración webOS](https://www.home-assistant.io/integrations/webostv/).

Los Fire TV pueden integrarse mediante ADB. Hace falta comprobar soporte del firmware, habilitación y autorización del dispositivo. El plan evaluará primero la vía que ya exponga Alexa y añadirá ADB solo cuando aporte funciones necesarias. [Integración de Fire TV por ADB](https://www.home-assistant.io/integrations/androidtv/).

### Ruta adicional de Alexa+

Amazon dispone de un MCP Toolkit para complementos de Alexa+. Puede reutilizar un servidor MCP con Streamable HTTP y admite interfaces visuales MCP Apps. Esto es una vía adicional de entrada para las mismas capacidades de MAX. [MCP Toolkit](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-overview).

El QuickStart exige URL remota, OAuth propio compatible y una latencia de consulta inferior a 500 ms. Ese plazo favorece herramientas que consulten estado o creen trabajos rápidamente; una investigación larga necesitará trabajo y consulta de resultados. El ejemplo en-US no demuestra disponibilidad para es-MX ni para la cuenta del propietario. [Requisitos de Alexa+ MCP](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-quickstart).

Decisión: la skill clásica con modo max será la entrada inicial. La elegibilidad de Alexa+ en la cuenta, locale y dispositivos se verificará como una prueba separada. Ambos canales compartirán el núcleo y los adaptadores.

## Arquitectura propuesta

~~~mermaid
flowchart TD
  U[Persona en Echo o Fire TV] --> A[Servicio de Alexa]
  A --> T[HTTPS de entrada]
  subgraph L[Laptop Linux en la red local]
    V[Adaptador de voz MAX]
    R[Enrutador y permisos]
    F[Acciones rápidas]
    J[Trabajos y sesiones persistentes]
    C[Codex como proceso local]
    M[Herramientas MCP y adaptadores]
    H[Home Assistant]
    P[Panel local y resultados]
    V --> R
    R --> F
    R --> J
    F --> H
    J --> C
    C --> M
    M --> H
    J --> P
  end
  T --> V
  C --> O[Inferencia autorizada con ChatGPT]
  H --> D[LG y dispositivos de la casa]
  H --> E[Funciones y anuncios en Alexa]
  J --> V
~~~

Componentes y responsabilidades:

| Componente | Responsabilidad propuesta |
| --- | --- |
| Adaptador Alexa | Validar solicitudes, extraer intent y sesión, devolver voz y visuales |
| Enrutador | Resolver controles conocidos con rapidez y derivar objetivos complejos |
| Motor Codex | Razonar, utilizar herramientas y ejecutar trabajos de proyectos |
| Registro de capacidades | Declarar herramientas disponibles, argumentos, permisos y versiones |
| Home Assistant | Mantener entidades, estados y adaptadores domésticos |
| Gestor de trabajos | Persistir estado, cancelación, progreso, plazos y reintentos |
| Almacenamiento | Separar hogares, personas, sesiones, memoria y resultados |
| Panel local | Conexión ChatGPT, dispositivos, tareas, fuentes y autorizaciones |

Para desarrollo se propone un endpoint HTTPS de la skill conectado a Linux mediante un túnel saliente. Cloudflare Tunnel es una opción, no un requisito de diseño exclusivo. Solo se publicará la entrada necesaria para Alexa; el panel, Home Assistant y el proceso Codex mantendrán su acceso local. [Funcionamiento de Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/).

El SDK de Alexa ofrece soporte para verificar firmas y marcas de tiempo de los web services. La implementación usará esa verificación y comprobará el identificador de la skill, en lugar de confiar únicamente en una URL difícil de adivinar. [Verificación con ASK SDK Python](https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit-sdk-for-python/host-web-service.html).

Alternativa posterior: Lambda y un relay/cola con conexión saliente desde Linux. Se comparará si el túnel no satisface los requisitos de despliegue o disponibilidad. Esta alternativa añade infraestructura y no se necesita para la primera prueba.

## Autenticación y separación de identidades

Hay dos vínculos independientes:

- **ChatGPT a MAX:** el propietario autoriza inferencia para la instalación. Los tokens quedan en el almacén protegido del host.
- **Alexa a MAX:** la cuenta de Alexa se vincula al hogar/usuario de MAX mediante credenciales emitidas por MAX.

El segundo vínculo no se resolverá pasando los tokens de ChatGPT a Alexa. El OAuth de una skill enlaza la cuenta del servicio propio. [Account linking de skills](https://developer.amazon.com/docs/alexaplus/account-linking/account-linking-for-custom-skills).

El callback SiWC de loopback debe ejecutarse donde está el navegador que inicia sesión. Para un Linux sin escritorio se seguirá un procedimiento de incorporación local o transferencia protegida documentado para hosts propios, conservando la identidad distinta del host. [Hosts remotos propios](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms).

El modelo de datos separará hogar, cuenta Alexa, dispositivo de origen y sesión. La identidad de voz se considerará una ayuda contextual; las operaciones que requieran identidad fuerte utilizarán el panel autenticado. El rol invitado no tendrá acceso a repositorios, documentos ni cuentas personales.

La renovación de tokens será serializada por cuenta para evitar que dos procesos sobrescriban credenciales renovadas. Los secretos no formarán parte de prompts, resultados de herramientas ni registros de voz.

## Cómo se ejecutarán las solicitudes

### Control rápido

Ejemplo: Max, enciende el TV de la sala.

1. Resolver el dispositivo y la acción contra el inventario y los alias.
2. Validar que la acción está permitida para ese hogar y canal.
3. Consultar el estado cuando sea necesario.
4. Ejecutar turn_on mediante el adaptador preferido.
5. Confirmar el estado observado o informar que la orden se envió y la verificación sigue pendiente.
6. Registrar el identificador de solicitud para impedir duplicados.

Las operaciones conocidas podrán ejecutarse sin una consulta al modelo. Codex intervendrá cuando haga falta interpretar un objetivo ambiguo, combinar capacidades o preparar un plan.

### Investigación o trabajo largo

Ejemplo: Max, busca información sobre un tema, compara fuentes y prepara un resumen.

1. Crear un trabajo persistente.
2. Intentar resolverlo dentro del presupuesto de voz si es breve.
3. Si va a tardar, responder antes del plazo de Alexa con su estado y forma de consultarlo.
4. Ejecutar búsqueda, lectura, síntesis y comprobación de fuentes.
5. Guardar un resumen para voz y un resultado detallado para pantalla.
6. Permitir consultar el resultado, continuar o cancelar.
7. Entregar avisos en el equipo apropiado cuando el usuario haya habilitado ese canal.

La entrega proactiva oficial de skills usa esquemas y permisos específicos. No se asumirá que permite leer cualquier resultado automáticamente fuera de una sesión. Los avisos por Alexa Devices serán una capacidad diferenciada y opcional; consultar resultados desde la skill y el panel será la base. [Esquemas de eventos proactivos](https://www.developer.amazon.com/en-US/docs/alexa/smapi/schemas-for-proactive-events.html).

Estados propuestos: en cola, ejecutando, esperando información, esperando autorización, completado, fallido y cancelado. Un stream interrumpido nunca se marcará como éxito.

## Capacidades que puede incorporar MAX

Estas son propuestas de producto; cada una requiere un adaptador funcional y sus pruebas.

| Capacidad | Ejemplo de uso | Dependencias y etapa |
| --- | --- | --- |
| Conversación contextual | Explícame esto y después hazme preguntas | SiWC, sesiones aisladas; MVP |
| Búsqueda fundamentada | Investiga un tema y resume las fuentes | Búsqueda disponible o adaptador alternativo; MVP |
| Control doméstico | Enciende el TV, ajusta volumen y cambia entrada | webOS y Home Assistant; MVP |
| Funciones de Alexa | Pide reproducción, ejecuta una solicitud nativa o una rutina compatible | Alexa Devices; prueba específica en MVP |
| Escenas compuestas | Prepara la sala para ver una película | Entidades y escenas realmente disponibles; etapa posterior |
| Trabajos de programación | Revisa un proyecto, reproduce un error y prepara un cambio con pruebas | Codex y workspace permitido; etapa de herramientas |
| Documentos y hojas de cálculo | Resume un PDF o prepara un informe | Extracción y herramientas locales autorizadas; etapa de herramientas |
| Asistencia de agenda | Revisa mi calendario y prepara mi día | OAuth independiente del proveedor; etapa de conectores |
| Automatizaciones con contexto | Avísame cuando termine un proceso o cambie un sensor | Eventos de Home Assistant, scheduler y canal autorizado |
| Memoria controlable | Recuerda mis preferencias y permite revisarlas o borrarlas | Almacenamiento por usuario, fuente y retención |
| Supervisión de proyectos propios | Consulta fallos o estados de servicios y prepara un diagnóstico | Adaptadores de lectura; acciones posteriores con permisos |
| Información visual | Muestra un resumen y sus fuentes en una pantalla compatible | Panel y, donde corresponda, APL |
| Lavadora y otros equipos | Consulta el estado a través del MCP existente | Validar primero el conector del proyecto previo; lectura inicial |
| Visión doméstica futura | Explica una imagen de una cámara enlazada | Cámara autorizada y modelo con soporte de imágenes |
| Voz MAX propia futura | Usar un cliente o satélite con una activación propia | Hardware de audio, reconocimiento y síntesis independientes |

APL puede acompañar las respuestas de la skill en dispositivos compatibles con pantalla. La implementación comprobará las interfaces declaradas por cada solicitud antes de enviar visuales. [Visuales y audio en skills](https://developer.amazon.com/en-US/docs/alexa/alexa-presentation-language/add-visuals-and-audio-to-your-skill.html).

La inspiración en Jarvis se traducirá en continuidad entre conversaciones y acciones, estado verificable, iniciativa configurable y resultados visibles. La identidad pública del proyecto será MAX; no utilizará material protegido de Iron Man para su distribución.

## Software y repositorios evaluados

Las licencias indicadas corresponden a los archivos consultados en la fecha de investigación. Antes de incorporar una dependencia se fijarán versión y avisos de distribución.

| Proyecto | Uso propuesto | Licencia consultada | Decisión inicial |
| --- | --- | --- | --- |
| [Codex](https://github.com/openai/codex) | Motor local y SDK | [Apache 2.0](https://github.com/openai/codex/blob/main/LICENSE) | Núcleo; validar versión compatible |
| [ASK SDK Python](https://github.com/alexa/alexa-skills-kit-sdk-for-python) | Solicitudes y respuestas de Alexa | [Apache 2.0](https://github.com/alexa/alexa-skills-kit-sdk-for-python/blob/master/LICENSE) | Mantener el ecosistema Python |
| [Home Assistant](https://github.com/home-assistant/core) | Integraciones domésticas y MCP | [Apache 2.0](https://github.com/home-assistant/core/blob/dev/LICENSE.md) | Base para dispositivos |
| [FastAPI](https://github.com/fastapi/fastapi) | API local, panel y entrada de voz | [MIT](https://github.com/fastapi/fastapi/blob/master/LICENSE) | Servicio MAX propuesto |
| [Authlib](https://github.com/authlib/authlib) | OAuth y validación de identidad | [BSD 3-Clause](https://github.com/authlib/authlib/blob/main/LICENSE) | Evaluar para SiWC y vínculo Alexa |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | Herramientas interoperables | [MIT](https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE) | Preferir SDK oficial |
| [aioamazondevices](https://github.com/chemelli74/aioamazondevices) | Biblioteca utilizada por Alexa Devices | [Manifest de la integración](https://github.com/home-assistant/core/blob/dev/homeassistant/components/alexa_devices/manifest.json) | Utilizar a través de Home Assistant |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | Navegación para tareas que necesiten navegador | [Apache 2.0](https://github.com/microsoft/playwright-mcp/blob/main/LICENSE) | Opcional, con perfil aislado |
| [Trafilatura](https://github.com/adbar/trafilatura) | Extraer texto y metadatos de páginas | [Apache 2.0](https://github.com/adbar/trafilatura/blob/master/LICENSE) | Adaptador de lectura |
| [SearXNG](https://github.com/searxng/searxng) | Metabúsqueda alojada por el usuario | [AGPL 3.0](https://github.com/searxng/searxng/blob/master/LICENSE) | Alternativa opcional de búsqueda |
| [Node-RED](https://github.com/node-red/node-red) | Flujos persistentes de eventos | [Apache 2.0](https://github.com/node-red/node-red/blob/main/LICENSE) | Reutilizar si facilita automatizaciones |
| [cloudflared](https://github.com/cloudflare/cloudflared) | Túnel saliente para entrada HTTPS | [Apache 2.0](https://github.com/cloudflare/cloudflared/blob/master/LICENSE) | Opción de despliegue |
| [SiWC DevKit](https://github.com/openai/sign-in-with-chatgpt-devkit) | Referencia de experiencia y flujo | [Licencia no comercial propia](https://github.com/openai/sign-in-with-chatgpt-devkit/blob/main/LICENSE) | No incorporarlo como base permisiva |

El DevKit no tiene una licencia MIT o Apache: su licencia restringe el uso a propósitos no comerciales. Para mantener el objetivo de una base ampliamente reutilizable, la propuesta es implementar el flujo documentado con código propio y bibliotecas compatibles, sin copiar el DevKit. Esto no modifica los requisitos ni las condiciones del servicio de ChatGPT.

SQLite y asyncio serán suficientes para una primera implementación de sesiones y trabajos. Redis o una plataforma de workflows solo se añadirán si las pruebas de concurrencia y recuperación lo justifican. Una base vectorial no será un requisito para empezar: se puede utilizar búsqueda local por texto y memoria explícita.

SearXNG es una alternativa independiente a la búsqueda del proveedor; su disponibilidad depende de los motores que consulte. Playwright se reservará para páginas interactivas o tareas que lo necesiten. Los resultados de páginas se tratarán como datos y no como instrucciones para controlar la casa.

Alexa Media Player es otra integración comunitaria que declara utilizar un API no oficial. Se evaluará únicamente si Alexa Devices no cubre una necesidad concreta. No conviene sostener el MVP sobre dos integraciones de Amazon con sesiones duplicadas. [Proyecto Alexa Media Player](https://github.com/alandtse/alexa_media_player).

## Referencias de asistentes reutilizables

| Referencia | Ideas útiles para MAX | Forma de aprovecharlas |
| --- | --- | --- |
| [OpenClaw](https://github.com/openclaw/openclaw) | Gateway persistente, canales, memoria y separación entre control y ejecución | Comparar arquitectura y una posible integración; no es una dependencia decidida |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Memoria de tareas, skills derivadas de procesos repetidos y trabajos programados | Inspiración para flujos y experiencia |
| [Leon](https://github.com/leon-ai/leon) | Rutas deterministas y rutas con agente, contexto local y voz | Referencia para combinar controles rápidos y objetivos abiertos |

El primer experimento comparará el coste de un núcleo específico de MAX frente a utilizar un gateway existente con un adaptador Alexa. Si un proyecto existente aporta claramente sesiones, trabajos y canales sin comprometer la integración solicitada, se documentará esa elección. El repositorio LUTS-IA seguirá siendo el proyecto principal y no se convertirá en un fork de esas referencias.

## Skills y herramientas de MAX

Una skill de Alexa define cómo se entra por voz. Una Agent Skill define un procedimiento reutilizable. Un servidor MCP implementa herramientas con datos y acciones. Mantener esas responsabilidades separadas evita prometer que un texto de instrucciones crea por sí mismo una capacidad. [Relación entre skills y MCP](https://developers.openai.com/plugins/concepts/skills).

Paquetes propuestos:

| Skill | Procedimiento |
| --- | --- |
| max-home | Resolver habitaciones y dispositivos, comprobar estados y ejecutar acciones permitidas |
| max-research | Buscar, contrastar, citar y producir versión breve y detallada |
| max-projects | Trabajar en un workspace permitido, verificar y presentar resultados |
| max-documents | Leer y crear artefactos utilizando herramientas instaladas |
| max-routines | Convertir objetivos repetidos en flujos revisables |
| max-memory | Guardar preferencias explícitas, mostrar su origen y permitir borrado |
| max-briefing | Componer un resumen con fuentes y conectores habilitados |
| max-diagnostics | Revisar servicios y equipos propios con herramientas de lectura |

Se utilizará el formato abierto SKILL.md con instrucciones, recursos y scripts opcionales. Las skills se cargarán según la tarea y las dependencias del runtime estarán declaradas. [Formato y carga en Codex](https://learn.chatgpt.com/docs/build-skills), [especificación abierta](https://agentskills.io/specification).

Los plugins y conexiones de esta conversación no se transfieren automáticamente al proceso de MAX. Cada integración de correo, calendario, GitHub o almacenamiento requerirá herramientas instaladas y su autorización correspondiente. Los conectores alojados no se supondrán disponibles por el mero inicio de sesión con ChatGPT.

Las nuevas skills podrán proponerse a partir de tareas repetidas, pero su activación, herramientas y versiones pasarán por revisión y pruebas. La lista de capacidades instaladas será visible.

## Permisos, memoria y comportamiento operativo

El sistema tendrá perfiles para propietario, miembro del hogar e invitado. Habrá capacidades habilitables de lectura, control doméstico cotidiano, edición de proyectos y operaciones externas. El objetivo es que los controles ordinarios ya autorizados sean fluidos y que las acciones de mayor impacto se revisen de forma concreta.

Decisiones de implementación propuestas:

- Separar herramientas de casa de ejecución de código y navegador.
- Utilizar cuentas de servicio y workspaces acotados para los trabajos.
- Evitar acceso administrativo general al MCP de Home Assistant como configuración inicial.
- Asociar cada solicitud a su hogar, dispositivo y permisos; no compartir un historial global.
- Deduplicar por requestId y jobId; serializar acciones sobre el mismo dispositivo.
- Preferir acciones que establezcan estado, como encender, frente a alternar sin conocerlo.
- Si hay un timeout tras enviar una orden, comprobar el estado antes de repetirla.
- Distinguir acción confirmada, enviada, fallida y pendiente.
- Mantener historial y memoria con retención configurable y borrado por usuario.
- Ocultar credenciales y contenido privado en los registros.
- Proteger la interfaz de administración con autenticación local.
- Permitir cancelar trabajos, pausar automatizaciones y deshabilitar conectores.
- Aplicar horarios y dispositivo de destino a los avisos.
- Tratar páginas web, documentos y respuestas de herramientas como información externa.

La revisión de una acción mostrará el efecto concreto, el destino y los datos que saldrán del sistema. No se basará únicamente en un mensaje genérico del modelo.

## Infraestructura necesaria

La siguiente configuración recoge los objetivos de ingeniería del MVP. El perfil verificado de la laptop satisface sus objetivos iniciales de memoria y almacenamiento; el rendimiento se medirá con la carga real:

| Elemento | Propuesta |
| --- | --- |
| Equipo | Laptop Linux conectada a la misma LAN |
| Memoria | 8 GB como objetivo inicial; 16 GB darán margen a navegador y servicios |
| Disco | SSD y aproximadamente 20 GB libres para runtime, contenedores y primeros datos |
| Conexión | Ethernet preferente si está disponible; evitar suspensión mientras preste el servicio |
| Inferencia | Cuenta ChatGPT elegible con permiso para uso del plan por MAX |
| Casa | Home Assistant Container en Linux o una instalación previa verificada |
| Servicios | MAX, worker Codex y almacenamiento persistente |
| Voz | Cuenta Amazon Developer, skill de desarrollo y equipos asociados |
| Acceso desde Alexa | Endpoint HTTPS válido y verificación de solicitudes |
| Operación | Copia de seguridad, registro de versiones, recuperación y restauración probada |

Home Assistant documenta tanto su instalación en VM como en contenedor sobre Linux. Su despliegue deberá preservar el descubrimiento y el acceso a la LAN. [Instalación Linux](https://www.home-assistant.io/installation/linux).

El uso de Home Assistant Cloud/Nabu Casa puede facilitar algunas integraciones, pero no será un requisito impuesto al proyecto. Si se utiliza la integración Alexa Smart Home para exponer entidades, se podrá comparar la configuración manual con el servicio Cloud. [Opciones de Alexa Smart Home](https://www.home-assistant.io/integrations/alexa.smart_home/).

El presupuesto operativo debe contemplar el uso del plan ChatGPT, electricidad, almacenamiento y cualquier proveedor opcional. El código abierto no convierte en ilimitados los servicios de terceros. El panel mostrará límites y errores de cuota de forma comprensible.

Alexa y la inferencia en la nube requieren sus servicios disponibles. En una caída de Internet, el panel local y las automatizaciones locales podrán seguir funcionando según sus adaptadores. Una voz totalmente local sería una etapa distinta.

## Plan de acción con entregables y aceptación

| Etapa | Trabajo | Criterio para avanzar |
| --- | --- | --- |
| 0. Inventario y decisiones | Completar equipos, registrar el Linux ya inspeccionado, revisar las vinculaciones de Home Assistant, fijar idioma y cuenta de pruebas | Equipos asociados a habitación y perfiles de servicios documentados |
| 1. Prueba SiWC y Codex | Incorporación propia, modelos, inferencia, renovación, interrupción y reanudación | Turno completado con el plan autorizado y herramientas locales de prueba |
| 2. Prueba de voz modo max | Modelo es-MX, comandos portadores, ayuda, cancelación, sesiones y endpoint válido | Invocación y captura verificadas en cada equipo disponible |
| 3. Acciones domésticas | Emparejar LG, asociar Fire TV, configurar Alexa Devices y herramientas permitidas | Control verificable del LG y una función nativa de Alexa |
| 4. Búsqueda y trabajos | Fuentes, extracción, resumen, cola, consulta y cancelación | Petición lenta sobrevive al plazo de Alexa y devuelve fuentes |
| 5. MVP integrado | Unir voz, Codex, control y panel; probar reinicios, duplicados y fallos | Demostración completa con aislamiento entre sesiones |
| 6. Extensiones de MAX | Skills, documentos, proyectos, conectores, memoria y flujos | Cada módulo con permisos, pruebas y documentación propios |
| 7. Distribución pública | Instalador, contenedores, CI, licencia, guías, matriz de compatibilidad y versiones | Instalación reproducible desde una máquina limpia |
| 8. Investigación de voz avanzada | Alexa+ MCP, visuales y posible satélite MAX | Viabilidad y disponibilidad confirmadas; decisión separada |

Las etapas 1, 2 y 3 reducen las principales incertidumbres antes de ampliar el producto. Se evitará construir primero un panel grande o instalar muchas integraciones sin comprobar esas tres bases.

El MVP abarcará conversación, control del TV, al menos una acción nativa, búsqueda con fuentes y trabajos consultables. La agenda, edición de proyectos, documentos, cámaras y automatizaciones amplían el producto después de esa base.

## Pruebas que definirán la calidad

Los siguientes valores son objetivos de diseño, no mediciones actuales:

- Respuesta de aceptación y control simple con presupuesto interno de seis segundos como máximo, dejando margen al plazo de Alexa.
- Objetivo de reconocimiento de al menos 90 % sobre un corpus inicial de expresiones de prueba, medido por equipo e idioma.
- Cero ejecuciones adicionales en las pruebas de entrega duplicada.
- Historial de dos sesiones y dos perfiles sin intercambio de contexto.
- Trabajo largo recuperable tras reiniciar el servicio, con estado y resultado coherentes.

Pruebas funcionales previstas:

1. Abrir modo max desde cada equipo y ejecutar ayuda/salir.
2. Capturar una consulta abierta con la frase portadora prevista.
3. Encender el LG desde apagado y verificar la vía real de encendido.
4. Cambiar volumen o entrada sin afectar otro equipo.
5. Ejecutar una función nativa en el dispositivo elegido.
6. Realizar búsqueda, abrir fuentes y conservar sus enlaces.
7. Resolver una petición que tarde más de ocho segundos sin bloquear la skill.
8. Consultar y cancelar un trabajo.
9. Repetir el mismo requestId sin duplicar la acción.
10. Interrumpir la red y mostrar estado pendiente o error real.
11. Renovar sesión ChatGPT y comprobar recuperación tras revocación.
12. Aislar consultas de propietario e invitado.
13. Leer una página con instrucciones ajenas sin convertirlas en acciones domésticas.
14. Recuperar la cola y las sesiones después de reinicio.
15. Comprobar que un éxito de transporte no se anuncia como éxito físico sin evidencia.
16. Verificar un resultado visual solo en equipos con la interfaz correspondiente.

Las pruebas automáticas cubrirán enrutamiento, identidad, permisos, deduplicación, almacenamiento y plazos con dobles de herramientas. Las pruebas en hardware comprobarán reconocimiento, emparejamiento, encendido y efectos reales. La matriz registrará generación/firmware, idioma y fecha de cada resultado.

## Organización y versión del repositorio original

La implementación podrá añadir un servicio MAX, despliegue, pruebas y skills al repositorio actual, manteniendo la carpeta Alexa como punto de entrada durante la transición. Las demás versiones de PC seguirán su historial y alcance actuales.

La propuesta de distribución es Apache 2.0 para el código propio de MAX, con atribuciones y avisos de dependencias. El repositorio actual no muestra un archivo LICENSE en su inventario; su publicación como open source necesita una licencia explícita y revisar los derechos del material existente antes de aplicarla.

Los cambios se organizarán en ramas de trabajo dentro del mismo repositorio y commits por etapa. No habrá un fork. Las releases incluirán notas, dependencias fijadas y un procedimiento de reversión. Credenciales, datos reales de red, identificadores de cuentas y conversaciones permanecerán fuera de Git.

Estructura futura orientativa:

| Ubicación | Contenido |
| --- | --- |
| 1 LUTSIA-ALEXA | Modelo y adaptador de voz en transición |
| max | Núcleo, motores, sesiones, permisos y trabajos |
| integrations | Adaptadores de casa y servicios |
| .agents/skills | Procedimientos reutilizables de MAX |
| deploy | Contenedores y operación en Linux |
| tests | Pruebas de componentes e integración |
| docs/max | Arquitectura, decisiones y guías |

## Incertidumbres que resolverá la primera etapa

- La Echo Dot todavía no está asociada a una IP o identidad verificable; se contrastará con la app Alexa y los eventos de la skill.
- El descubrimiento adicional de Echo Show 5 requiere confirmar su habitación y papel en las pruebas.
- La laptop Linux ya está identificada e inspeccionada; falta medir el comportamiento de MAX con su carga real.
- Home Assistant Linux ya está comprobado; faltan las vinculaciones específicas de webOS, Alexa Devices y MCP y la estrategia de actualización de versión.
- La cuenta Amazon, marketplace, idioma y estado de publicación de la skill actual deben revisarse.
- La disponibilidad de Alexa+ MCP en la cuenta y en español no se deduce de sus ejemplos.
- El soporte de búsqueda y del modelo elegido debe verificarse con el grant real de SiWC.
- El encendido del LG y la cobertura real de Fire TV/Alexa se comprobarán por función.

La siguiente unidad de trabajo propuesta es completar el inventario y realizar las tres pruebas de viabilidad: SiWC con Codex, invocación modo max y control doméstico. Después se implementará el MVP alrededor de los resultados observados.
