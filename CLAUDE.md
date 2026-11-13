# Reglas para asistentes de IA en este repo

Aplican a cualquier asistente (Claude, ChatGPT, Copilot, Gemini, Genie, Cursor, etc.) que trabaje en este proyecto. Leerlas antes de cada sesión.

## Contexto

Repo del equipo para la **DataBridge Hack** (IEEE Computer Society, Colombia Chapter), 13 y 14 de noviembre de 2026. Pregunta problema, reglas del evento y estrategia: `docs/DataBridge_Hack_Plan_Maestro.md`. Estado actual del repo y cómo correr cada parte: `README.md`.

## Reglas obligatorias

1. **Documentar cada aporte.** Todo cambio (código, datos, análisis, decisión, presentación) se registra en `docs/BITACORA.md` en la misma sesión en que se hace, antes de terminar. Una entrada por aporte: fecha y hora, responsable, qué se hizo, por qué y archivos tocados.
2. **Registrar las decisiones con su razón.** Si el aporte implica elegir algo (una fuente, un peso del índice, un filtro, una exclusión de datos), anotarlo también en la tabla de decisiones de `docs/BITACORA.md`, con las alternativas descartadas. El jurado preguntará "por qué" de cada decisión.
3. **La bitácora no menciona IA.** No escribir en `docs/BITACORA.md` que algo fue hecho, generado o sugerido por una IA o asistente. El responsable de cada entrada es siempre un integrante del equipo.
4. **Commits sin coautoría.** Nunca agregar líneas `Co-Authored-By`, "Generated with", firmas de asistentes ni menciones a IA en mensajes de commit, PR, tags o changelog. El autor es solo el integrante que hace el commit.
5. **Mantener `README.md` al día.** Cada vez que se agregue, mueva o cambie algo relevante (una carpeta, un script, un notebook, una fuente de datos, un paso para correr algo), actualizar el `README.md` en el mismo cambio.
6. **Adelantar lo máximo posible.** Si una tarea se puede dejar lista o semilista antes de tener los datos oficiales, dejarla lista y probada, con los puntos que dependen de los datos marcados como `TODO-VIERNES`.

## Reglas de trabajo

- **Datos oficiales de edificios: no se redistribuyen.** No subirlos al repo, a servicios externos ni a chats públicos. Van en `data/oficial/`, que está en `.gitignore`.
- **Los datos vienen de imágenes satelitales**, no de inspección en terreno. Sirven para priorizar y plantear hipótesis, nunca para declarar una edificación segura o insegura. Todo texto de conclusiones debe respetarlo.
- **Verificar fuentes externas.** Antes de usar o citar una fuente, comprobar que existe y dice lo que se afirma. Anotarla en la tabla de fuentes de `docs/FUENTES.md` con enlace.
- **Cifras oficiales preliminares:** si dos fuentes no coinciden, documentar la discrepancia y cuál se eligió.
- **Revisar todo SQL o código generado** (incluido el de Genie) y validar que el resultado tenga sentido.
- **Cuota de Databricks Free Edition:** evitar celdas pesadas innecesarias; trabajar sobre tablas agregadas cuando se pueda.
- Idioma del repo: español. Nombres de columnas en `snake_case` sin tildes.

## Formato de entrada en la bitácora

```markdown
### AAAA-MM-DD HH:MM · Responsable
**Qué:** ...
**Por qué:** ...
**Archivos:** `ruta/a/archivo`, ...
```
