# Guía LUTS-IA 📘

---

## Introducción

Te damos la bienvenida a **LUTS-IA** 🌐. Esta es tu plataforma para explorar y experimentar con ChatGPT y otras tecnologías interactivas. Imagina charlar con dispositivos como Alexa o aplicaciones en tu computadora, como si estuvieras hablando con un ser humano 💬🖥️. Aquí te enseñaremos cómo hacerlo realidad.

La guía que tienes en tus manos es tu brújula 🧭 en esta emocionante aventura digital. No importa si eres nuevo en el mundo tecnológico o si ya tienes experiencia; hemos diseñado esta guía pensando en todas las personas. Explicamos cada paso de forma clara y sencilla, para que nadie se quede atrás 🚶‍♂️.

Entonces, si estás listo para embarcarte en un viaje de descubrimiento hacia las profundidades de la interacción digital, ¡continúa leyendo! 🚀🌌



Te damos la bienvenida a **LUTS-IA** 🌐, tu puerta de entrada al mundo de ChatGPT y la interactividad. ¿Te has imaginado charlar con dispositivos como Alexa o aplicaciones en tu computadora? 💬🖥️ ¡Estás en el sitio perfecto! 📍

Esta guía es como tu brújula 🧭 en esta aventura. No te preocupes si no eres un experto en tecnología 🤷; hemos diseñado cada parte pensando en ti. Todo está explicado de forma sencilla y paso a paso 🚶‍♂️.

Así que, ¡empecemos! 🚀 Estás a punto de embarcarte en un viaje fascinante hacia el núcleo de la interacción digital 🌌. ¡Vamos allá! 🎉

---

## Capítulo 1: Conexión con OpenAI

Para experimentar con ChatGPT, Alexa y otras interacciones, es esencial tener una conexión con OpenAI. La buena noticia es que obtener esta conexión es sencillo. Aquí te mostramos cómo hacerlo a través de una API Key:

### 📝 Guía para Registrarse en OpenAI y Obtener una API Key

- **Registrarse en OpenAI 🖊️**
  1. **Acceder al Sitio Oficial**: Dirígete a [OpenAI](https://www.openai.com/).
  2. **Registro**: Haz clic en "Get started" en la esquina superior derecha.
  3. **Detalles**: Proporciona tu dirección de correo electrónico, contraseña y cualquier otra información solicitada.
  4. **Confirmar Correo**: Valida tu dirección de correo a través del enlace que recibirás.
  
- **Iniciar sesión en OpenAI 🖥️**
  1. **Acceder al Sitio Oficial (nuevamente)**: Dirígete a [OpenAI](https://www.openai.com/).
  2. **Iniciar Sesión**: Haz clic en "Log in", que se encuentra al lado izquierdo del botón "Get started".
  3. **Ingreso de Credenciales**: Ingresa con tu correo y contraseña.
  
- **Acceder a la Plataforma de la API de OpenAI 🌍**
  1. **Elegir la Opción API**: Una vez que hayas iniciado sesión, verás tres opciones: "ChatGPT", "DALL-E", y "API". Haz clic en "API".
  2. **Redirección**: Serás redirigido a [platform.openai.com](https://platform.openai.com/).
  3. **Acceder a las API Keys**: En la esquina superior derecha, haz clic en "Personal", luego en el menú desplegable selecciona "View API keys".
  
- **Crear una nueva API Key 🔑**
  1. **Generación de Key**: En el medio de la página, busca y haz clic en el botón que dice "+ Create new secret key".
  2. **Información Adicional**: Llena cualquier campo o formulario que se te solicite.
  3. **Recibir API Key**: Una vez creado, recibirás tu API key. **¡Guárdala con cuidado!**

---

## Capítulo 2: Integración con Alexa

Ahora que tienes tu API Key de OpenAI, es hora de llevar la interacción al siguiente nivel integrando ChatGPT con Alexa. Aquí te guiaré en cómo desarrollar tu propio skill de Alexa, que será la interfaz de tu proyecto LUTS-IA:

### 🚀 Empezando: La sinergia entre Alexa y ChatGPT

#### Pasos 📝

1. 🎤 Registrarte en Alexa Developer
2. 🎨 Desarrollando LUTS-IA en Alexa

### 1. 🎤 Registrarte en Alexa Developer:

**Nota:** Antes de continuar, necesitas una cuenta de Amazon. Si ya tienes una, puedes saltarte el primer paso

- **Cuenta Amazon**: 🛒 Dirígete a [Amazon](https://www.amazon.com/)., haz clic en "Iniciar sesión" y luego selecciona "Crear tu cuenta de Amazon".

- **Ir al Alexa Developer Console**: 🌐 Una vez que tengas tu cuenta de Amazon, visita [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask).

- **Iniciar sesión**: 🔑 Haz clic en "Iniciar sesión", si aún no iniciaste sesión, en la esquina superior derecha y utiliza tus credenciales de Amazon para acceder.

- **Perfil de desarrollador**: 📋 La primera vez que inicies sesión, se te pedirá que completes tu perfil de desarrollador. Esto incluye información básica como tu nombre, dirección y número de teléfono. Llena todos los campos obligatorios y haz clic en "Guardar".

- **Acuerdo de desarrollador**: 📜 Antes de empezar a crear skills para Alexa, tendrás que aceptar el Acuerdo de Desarrollador de Alexa. Léelo cuidadosamente y acepta los términos.

- **Dashboard de Alexa Developer Console**: 🖥️ Una vez que hayas aceptado el acuerdo, serás llevado al dashboard del Alexa Developer Console. Desde aquí, puedes comenzar a crear y gestionar tus skills de Alexa.

### 2. 🎨 Desarrollando LUTS-IA en Alexa:

Antes de sumergirnos en los pasos detallados, es esencial comprender qué es una "Skill" de Alexa. Una Skill de Alexa es similar a una aplicación para tu smartphone, pero diseñada específicamente para Alexa, la asistente virtual de Amazon. Estas Skills permiten a Alexa realizar tareas adicionales, desde contar chistes hasta controlar dispositivos inteligentes en tu hogar. Al desarrollar una Skill, estás esencialmente enseñando a Alexa una nueva habilidad que puede ser invocada mediante comandos de voz.

#### 1. 🛠️ Preparativos Iniciales:
- **Registro en Amazon Developer**: 🌐 Es la misma cuenta de Amazon que acabas de crear o la que ya tenías previamente. 
- **Registro en OpenAI**: 🤖 Recuerda registrarte en OpenAI y obtener una API Key.

#### 2. 🖥️ Acceso a la Consola de Alexa Skills Kit (ASK):
1. Dirígete a la [Consola de Alexa Skills Kit](https://developer.amazon.com/alexa/console/ask).
2. Haz clic en "Create Skill".

#### 3. 🛍️ Creación del Skill:
1. **Name**: Ingresa "LUTSIA Alexa".
2. **Locale**: Elige "Spanish (MX)".
3. **Type of Experience**: Selecciona "Other".
4. **Model**: Escoge "Custom".``
5. **Hosting**: Marca "Alexa-Hosted (Python)".
6. **Template**: Elige "Start from scratch".
7. Finalmente, haz clic en "Create Skill".

#### 4. 🔧 Configuración del Modelo de Interacción:
1. Haz clic en "JSON Editor" en el panel izquierdo.
2. Copia el contenido del archivo `JSON_Editor.js` que está en este repositorio en la carpeta /LUTS-IA Alexa y pégalo en el editor.
3. Guardalo (Save) y luego clic en Build Skill.

#### 5. 🖥️ Configuración del Backend en Alexa-Hosted:
1. Accede a la pestaña "Code".
2. Sustituye el contenido de `lambda_function.py` con el del archivo que encontrarás acá en GitHub /LUTS-IA Alexa.
3. Incorpora tu API key de OpenAI, en la línea de código que dice **openai.api.key = "COLOCA-TU-API-KEY"**
4. Sustituye el contenido del archivo `requirements.txt` con el que encontrarás en GitHub /LUTS-IA Alexa, en caso de no existir crea el archivo dando clic en el botón NewFile. 
5. Guarda y despliega el código dando clic en el botón Save tanto en el archivo lambda_function.py y el archivo requirements.txt y luego dale clic al botón Deploy

#### 6. 🎤 Prueba del Skill:
1. Haz clic en la pestaña "Test".
2. Activa las pruebas en - Skill testing is enabled in: "Development".
3. Pronuncia o escribe "Abrir modo u. t. s.".
4. Deberías recibir una respuesta de LUTS-IA.

---

## Capítulo 3: Guía de Instalación y Configuración para PC

### Instalación de Visual Studio Code

1. Visita la página oficial de [Visual Studio Code](https://code.visualstudio.com/).
2. Descarga la versión adecuada para tu sistema operativo.
3. Ejecuta el instalador y sigue las instrucciones.

### Configuración del Entorno Python en Visual Studio Code

1. Abre Visual Studio Code.
2. Ve al mercado de extensiones o pulsa `Ctrl+Shift+X`.
3. Busca y instala la extensión `Python` proporcionada por Microsoft.
4. Reinicia Visual Studio Code.

### Instalación de las Bibliotecas

1. Asegúrate de tener Python y pip instalados en tu sistema.
2. Crea una carpeta llamada `LUTS-IA` en tu sistema.
3. Coloca el archivo `requirements.txt` dentro de la carpeta `LUTS-IA`.
4. Abre Visual Studio Code.
5. Haz clic en `File` > `Open Folder` y selecciona la carpeta `LUTS-IA`.
6. Una vez dentro de la carpeta en Visual Studio Code, accede al terminal integrado haciendo clic en `Terminal` > `New Terminal` o presionando `Ctrl+` + `` ` `` (backtick).
7. En el terminal, escribe y ejecuta el siguiente comando:
   ```bash
   pip install -r requirements.txt
   ```

Esto instalará todas las bibliotecas y dependencias necesarias para ejecutar los scripts.

### ¿Como ejecutar del Código en Visual Studio Code?

1. Clic en File y en el menú desplegable clic en Open Folder y ubica la carpeta donde está tu proyecto LUTS-IA.
2. Abre el archivo `app.py` que deseas ejecutar.
3. En la esquina superior derecha, haz clic en el botón de `Play` o presiona `F5` para ejecutar el archivo.

---

## Capítulo 4: 💻 Versiones de LUTS-IA para PC
Para todas las versiones de PC, sigue estos pasos generales:

1. Descarga la carpeta correspondiente y colócala en tu PC 📂.
2. Usando Visual Studio Code, abre la carpeta.
3. En cada carpeta, debes crear un archivo llamado `.env` y copiar el contenido del archivo env.txt dentro de ese archivo📄. Modifica el texto (COLOCA-AQUI-TU-API-KEY-DE-OPEN-AI) con tu API Key de OpenAI. 🔑
4. Luego, solo tienes que abrir el archivo app.py 📜.
5. ¡Ejecuta el archivo! Puedes hacerlo presionando F5 o usando el comando de ejecución de Visual Studio Code 🚀.
6. Una vez que lo hagas, abre un navegador e ingresa a **http://127.0.0.1:5000** 🌍.


