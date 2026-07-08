# Playbook de prospección — Gestorías y asesorías (Vilanova i la Geltrú + Garraf)

**Objetivo único de esta campaña:** conseguir reuniones de diagnóstico **pagadas**.
No vender "IA", no vender un producto. La métrica de validación es: **1 diagnóstico
pagado en las primeras 4 semanas**. Si no llega, se revisa ángulo u oferta antes
de construir nada.

**Listado:** `outputs/prospector/prospectos_gestorias_vng.csv` (40 prospectos,
regenerable con `generar_prospectos_gestorias.py`). Filtrar por Tipo =
"gestoria/asesoria" para el ICP primario (29 despachos).

---

## 1. El ángulo (por qué esto y no "marketing digital")

A una gestoría no le faltan clientes: le sobra trabajo. Verifactu, registro
horario, cambios de convenios, requerimientos — la carga normativa crece cada
año y no encuentran personal cualificado. Su cuello de botella es interno:

- **Picar datos a mano** (facturas, DNI, escrituras → A3/Sage): 30-50% del
  tiempo del equipo administrativo en muchos despachos.
- **Responder "¿cómo va mi trámite?"** por teléfono y email todo el día.
- **Estar al día de normativa** robando horas de trabajo facturable.

El mensaje NUNCA es "inteligencia artificial". Es: **"te devuelvo horas de tu
equipo antes de que acabe el trimestre"**. La IA es el cómo, no el qué.

Regla sobre cifras: usar rangos prudentes ("despachos del sector reportan
reducir a la mitad el tiempo de volcado de facturas") y jamás prometer
porcentajes exactos que no podamos demostrar con SU caso.

---

## 2. La escalera de oferta

| Peldaño | Qué es | Precio | Para qué sirve |
|---|---|---|---|
| 1. Diagnóstico exprés | 2 semanas: mapear sus 3 trámites de más volumen, cronometrar dónde se van las horas, informe con plan y ROI estimado | 490 € (se descuenta del piloto si sigue) | Validar que pagan. Cero código. |
| 2. Piloto IDP | 6 semanas: extracción automática de facturas de proveedores + DNI/NIE con validación humana, volcado a su software (A3, Sage, Holded…) | 2.500–4.500 € según volumen | Primer resultado tangible y medible en horas |
| 3. Iguala mensual | Mantenimiento + ampliación (más tipos de documento, seguimiento de expedientes, avisos a clientes) | 300–600 €/mes | Recurrencia; land & expand |

**Garantía del piloto:** si al final de las 6 semanas no ahorra un mínimo de
horas acordado por escrito en el diagnóstico, se devuelve el 100% del piloto.
(El diagnóstico no se devuelve: es trabajo entregado.)

**La demo asesina:** en la reunión de diagnóstico, pedirle 10 facturas reales
y enseñarle la extracción estructurada en vivo. Preparar el pipeline de demo
ANTES de la primera reunión confirmada, no antes.

---

## 3. Secuencia de contacto (por prospecto)

Cadencia: máx. 10 prospectos nuevos/semana para poder personalizar de verdad.
Antes de escribir a nadie: visitar su web, apuntar nombre del titular/socio,
servicios que destacan y algo concreto (años en Vilanova, especialidad, equipo).

### Día 0 — Email 1 (el dolor, corto)

> **Asunto:** ¿Cuántas horas se van en picar facturas en [NOMBRE DESPACHO]?
>
> Hola [NOMBRE],
>
> Trabajo con despachos de la zona de Vilanova y la pregunta que más repito
> es esta: ¿cuántas horas a la semana se va tu equipo en pasar datos de
> facturas y DNI al [A3/Sage/su software]?
>
> En la mayoría de gestorías son 10-20 horas semanales. Con la carga que ha
> traído Verifactu y los cambios de convenios, es tiempo que no tenéis.
>
> Me dedico a automatizar exactamente eso: el documento llega por email o
> WhatsApp y entra solo en vuestro programa, con revisión humana final.
>
> ¿Te encaja que te lo enseñe con 10 facturas vuestras reales? 20 minutos,
> en vuestro despacho.
>
> [FIRMA — Luis, MerakIA, Vilanova i la Geltrú]

### Día 3-4 — Llamada de seguimiento

Objetivo: solo confirmar que llegó el email y proponer día. Guion abajo (§4).

### Día 7 — Email 2 (la prueba concreta)

> **Asunto:** 22 horas → 9 horas (caso real de gestoría)
>
> Hola [NOMBRE],
>
> Te escribí la semana pasada por el tema del volcado manual de datos.
> Un dato del sector: una gestoría de Madrid pasó de 22 a 9 horas semanales
> en tareas de volcado e informes automatizando la lectura de facturas.
>
> No te pido que te lo creas: te propongo medirlo en tu despacho. Hago un
> diagnóstico de 2 semanas (490 €, descontables si seguimos) donde cronometro
> vuestros 3 trámites de más volumen y te digo, con números, qué se puede
> automatizar y qué no vale la pena.
>
> Si el informe no te aporta nada, me lo dices a la cara — soy de aquí.
>
> ¿Miércoles o jueves de la semana que viene?
>
> [FIRMA]

### Día 14 — Email 3 (breakup con gancho normativo)

> **Asunto:** última — antes del próximo cambio de normativa
>
> Hola [NOMBRE],
>
> Cierro el hilo, que sé que estáis a tope (precisamente por eso escribía).
>
> Solo esto: cada cambio de normativa que viene os va a meter más papel,
> no menos. Los despachos de la zona que automaticen antes el trabajo
> repetitivo van a poder coger más clientes sin contratar. Los demás van
> a seguir rechazándolos.
>
> Si en algún momento quieres los 20 minutos con vuestras facturas, mi
> puerta está abierta — estoy en Vilanova.
>
> Un abrazo,
> [FIRMA]

### WhatsApp (solo si hay número móvil visible o tras contacto previo)

> Hola [NOMBRE], soy Luis, de MerakIA (Vilanova). Te mandé un email sobre
> el tiempo que se va en picar facturas a mano en el despacho. En 20 min te
> enseño cómo automatizarlo con vuestros propios documentos, sin cambiar de
> programa. ¿Te va bien un café esta semana?

---

## 4. Guion de llamada (día 3-4)

1. **Apertura (10 seg):** "Hola, soy Luis, de MerakIA, aquí en Vilanova.
   Le escribí un email el [día] sobre el volcado manual de facturas —
   ¿le suena? ¿Tiene 2 minutos?"
2. **Si no lo leyó:** "Se lo resumo: automatizo la entrada de datos de
   facturas y DNI al programa de gestión de despachos como el suyo. La
   pregunta clave: ¿cuántas horas a la semana se va su equipo en eso?"
3. **Escuchar.** Lo que diga aquí es oro: apuntarlo en el CRM literal.
4. **Cierre único:** "Le propongo enseñárselo con 10 facturas suyas reales,
   20 minutos en su despacho, sin compromiso. ¿Miércoles o jueves?"
5. **Si duda:** ofrecer el diagnóstico pagado como alternativa seria, no
   como rebaja: "Otra opción es empezar por un diagnóstico de 2 semanas
   donde le doy números de su propio despacho. Cuesta 490 € y se descuenta
   si seguimos trabajando."

**Nunca en la primera llamada:** hablar de RAG, LLMs, modelos, "agentes".
Palabras permitidas: automatizar, programa, horas, revisión humana, Verifactu.

---

## 5. Objeciones frecuentes

- **"Ya tenemos A3/Sage/Wolters"** → "Perfecto, no lo toco. Yo hago que los
  documentos entren solos ahí. El programa es el destino, no el problema."
- **"¿Y la protección de datos?"** → "Todo se procesa con contrato de encargo
  de tratamiento, y podemos trabajar con despliegue en servidores europeos o
  en local. Se lo dejo por escrito en el diagnóstico." (Y cumplirlo.)
- **"La IA se equivoca"** → "Por eso el diseño lleva siempre revisión humana:
  la herramienta rellena, una persona valida. El error de picar a mano
  cansado un viernes a las 19h es más caro."
- **"No tengo tiempo ni para esto"** → "Eso es exactamente el síntoma. El
  diagnóstico se lo hago yo; usted pone 1 hora en total."
- **"¿Cuánto cuesta?"** (pronto) → "Depende del volumen; por eso el primer
  paso es el diagnóstico de 490 €. Lo que le puedo asegurar es que el informe
  le dice también lo que NO vale la pena automatizar."

---

## 6. Higiene legal del outreach (no saltárselo)

- Email en frío B2B: dirigirse a la empresa/rol, no a particulares; incluir
  quiénes somos y cómo darse de baja ("si no quieres que te vuelva a escribir,
  dímelo y listo"). Nada de listas compradas: solo emails localizados en la
  web pública del despacho.
- No adjuntar PDFs pesados en el primer email (spam + desconfianza).
- Registrar en el CRM (`outputs/prospector/crm.db`) cada contacto y respuesta.

## 7. Métricas semanales (revisar cada viernes)

- Emails 1 enviados / respuestas (objetivo >10% con personalización real)
- Llamadas hechas / conversaciones reales
- Reuniones agendadas
- **Diagnósticos vendidos ← la única métrica que valida el vertical**

Criterio de parada: 4 semanas, ~40 prospectos trabajados, 0 diagnósticos
vendidos → parar y revisar (¿ángulo? ¿precio? ¿zona? ¿canal?) antes de
insistir o construir nada.
