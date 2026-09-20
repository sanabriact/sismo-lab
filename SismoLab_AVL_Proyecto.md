# SismoLab AVL

## Proyecto de estructuras de datos

# 1 Propósito y escenario

Diseñen e implementen una aplicación con interfaz gráfica para gestionar un observatorio sísmico simulado.

Su núcleo será un árbol AVL de eventos activos, cuyo orden dependerá de la prioridad de revisión, la magnitud y el identificador de cada terremoto.

El observatorio recibe información de varias estaciones (parametrizadas, pero inmutables durante la ejecución del sistema). Los reportes pueden llegar tarde, repetirse o corregir datos anteriores. Una corrección puede cambiar la prioridad de un evento y las asociaciones entre terremotos. Durante una ráfaga de reportes, el sistema podrá aplazar el balanceo y posteriormente recuperar el equilibrio del árbol.

El objetivo es construir una solución coherente y explicar cómo las abstracciones elegidas permiten conservar el orden, el balance y la consistencia del sistema. El proyecto utiliza reglas académicas y datos de un territorio ficticio; sus clasificaciones no constituyen un modelo de predicción ni una evaluación real del riesgo sísmico.

# 2 Alcance y decisiones de diseño

Son obligatorias las reglas de datos, prioridad, comparación e integridad descritas en este documento. Los equipos deben decidir cómo representarlas y cómo organizar la solución. Las decisiones abiertas deben documentarse, implementarse y sustentarse con ejemplos y análisis de costo.

- Definan las entidades y responsabilidades necesarias para distinguir eventos, reportes, estaciones, asociaciones, versiones y operaciones. No se prescribe un número de clases ni una arquitectura (aunque si debe haber una separación de GUI y negocio).
- Elijan las estructuras auxiliares, la representación de los nodos, el manejo del historial y el formato concreto del JSON. Justifiquen cada elección y las alternativas descartadas.
- Implementen el AVL y el BST de comparación. No se permite delegar sus operaciones a bibliotecas de árboles o colecciones ordenadas. Se pueden utilizar bibliotecas para interfaz gráfica, lectura de JSON, visualización y pruebas.
- Utilicen explícitamente una pila para deshacer y una cola para reportes pendientes. El equipo debe explicar su representación y el costo de sus operaciones.
- El AVL será la estructura central del catálogo activo. Las consultas y actualizaciones deben utilizarlo; no se admite resolver su gestión exclusivamente con una lista paralela que se ordena después de cada cambio.
- Las características físicas de un evento y sus asociaciones se conservarán por identidad. Las relaciones padre e hijo del AVL representan el orden de almacenamiento y pueden cambiar con las rotaciones.

# 3 Datos del escenario y de los eventos

El escenario contiene estaciones, zonas pobladas y no pobladas, eventos y un reloj de simulación. Las zonas son rectángulos definidos por sus límites en un plano de 0 a 1000 km en ambos ejes. Un epicentro pertenece a una zona cuando está dentro de ella o sobre su borde, cuando está en el borde de dos zonas, se clasifica como zona poblada si alguna de las dos está definida de esa forma. La geometría permanece fija durante el escenario.

| Dato | Regla obligatoria |
|---|---|
| **Identificador** | Entero entre 1 y 999999, único en el escenario. Puede mostrarse como SIS-000010. Se compara el valor numérico, no el texto. Es inmutable y no se reutiliza para otro terremoto. Se ingresa por parte del usuario de cada estación, por eso desde diferentes estaciones se puede notificar sobre el mismo evento. |
| **Magnitud M** | Número decimal finito entre -2,0 y 10,0, con máximo un decimal. Todos los eventos usan la misma escala dentro del simulador. |
| **Profundidad H** | Profundidad del hipocentro en km. Número finito entre 0,0 y 700,0, con máximo un decimal. |
| **Epicentro** | Coordenadas x e y en km, entre 0,0 y 1000,0, con máximo un decimal. Permiten determinar la pertenencia a zonas y las distancias. |
| **Fecha y hora** | Instante de ocurrencia en UTC, con precisión de segundos. En JSON se utiliza ISO 8601, por ejemplo `2026-09-07T10:00:00Z`. |
| **Revisión y procedencia** | Revisión entera positiva, comparable por evento, y estación que emite el reporte. Se conserva la revisión vigente y el conjunto de estaciones con reportes aceptados. |
| **Estado de atención** | Pendiente o revisado. Un alta inicia pendiente. Una corrección aceptada de sus datos lo devuelve a pendiente. |

El reloj de simulación es explícito y se guarda con el escenario. Los tiempos de ocurrencia no pueden ser posteriores a ese reloj. Su avance se realiza por una acción del usuario y determina la antigüedad de los eventos.

# 4 Cálculo obligatorio de la prioridad

La prioridad se deriva de los datos vigentes y no se introduce manualmente. Las siguientes reglas son fijas y se aplican en el orden indicado:

| Prioridad | Condición |
|---|---|
| **3 Alta** | M ≥ 6,0; o bien M ≥ 4,5 y H ≤ 30,0 km y epicentro en zona poblada. |
| **2 Media** | No cumple la condición de prioridad alta y M ≥ 4,5. |
| **1 Baja** | No cumple ninguna de las condiciones anteriores. |

Los límites son inclusivos. Por ejemplo, M = 4,5 y H = 30,0 km en zona poblada produce prioridad 3. El mismo evento fuera de una zona poblada produce prioridad 2.

# 5 Regla de inserción y orden del AVL

Cada nodo del AVL representa exactamente un evento activo. Su clave obligatoria es la tupla ordenada **K = (P, M, I)**, donde P es la prioridad calculada, M la magnitud vigente e I el identificador numérico.

## Comparación entre dos eventos

La comparación es lexicográfica: se utiliza el primer componente que sea diferente. La prioridad tiene precedencia sobre la magnitud y la magnitud tiene precedencia sobre el identificador.

- Si las prioridades difieren, es menor la clave del evento con menor prioridad.
- Si las prioridades son iguales, es menor la clave del evento con menor magnitud.
- Si prioridad y magnitud son iguales, es menor la clave del evento con menor identificador numérico.

En cada nodo visitado durante la inserción, una clave menor continúa por el hijo izquierdo y una clave mayor por el hijo derecho. Se repite la comparación hasta ubicar el nuevo nodo y se aplica el balanceo correspondiente al modo de ejecución.

Todos los nodos del subárbol izquierdo deben tener claves menores que la de su raíz, y los del derecho, claves mayores. El recorrido inorden produce claves ascendentes; el recorrido inverso produce claves descendentes. La raíz no tiene que ser el evento más prioritario.

## Ejemplo de comparación

Frente a un nodo cuya clave es `(3, 5.2, 10)`, se obtienen las siguientes decisiones. El punto se utiliza como separador decimal en las claves y en JSON.

| Clave entrante | Dirección | Motivo |
|---|---|---|
| `(2, 5.8, 20)` | Izquierda | La prioridad 2 es menor que 3, aunque 5.8 sea mayor que 5.2. |
| `(3, 6.1, 30)` | Derecha | Empatan en prioridad y 6.1 es mayor que 5.2. |
| `(3, 5.2, 5)` | Izquierda | Empatan prioridad y magnitud; 5 es menor que 10. |
| `(3, 5.2, 25)` | Derecha | Empatan prioridad y magnitud; 25 es mayor que 10. |

## Identidad y cambios de clave

Antes de crear un nodo se debe comprobar si su identificador ya existe, aunque la nueva información produzca otra clave. Un reporte del mismo identificador se tramita como confirmación, corrección o conflicto según la sección 6. Nunca se crea un segundo nodo para ese terremoto.

Si una corrección cambia P o M, el evento debe retirarse con su clave anterior y reinsertarse con la nueva, conservando su identificador. La actualización completa constituye una sola acción. El equipo decide cómo localizar el evento y conservar sus referencias sin dejar estados parciales.

La hora, la profundidad del nodo y el estado de atención no forman parte de K. La profundidad del hipocentro y la ubicación solo influyen en K mediante el cálculo de P. Las rotaciones no alteran los datos físicos ni la prioridad de un evento.

# 6 Gestión de eventos y revisiones

La interfaz gráfica debe permitir crear, consultar, corregir, marcar como revisado y eliminar individualmente un evento activo. Cada operación debe mostrar su resultado y actualizar el AVL, las asociaciones, las métricas, la visualización y el historial de acciones cuando corresponda.

## Creación manual de un evento

El usuario registrará el identificador, la magnitud, la profundidad del hipocentro, las coordenadas del epicentro, la fecha y hora de ocurrencia y la estación que origina el registro. Antes de insertar, el sistema valida los rangos y comprueba que el identificador no pertenezca a un evento activo, archivado o eliminado.

Si los datos son válidos, el sistema debe ejecutar la creación como una sola acción:

- Asignar la revisión 1, calcular la pertenencia a una zona poblada y derivar la prioridad.
- Construir la clave `K = (P, M, I)`, insertar el evento según las reglas del AVL y marcarlo como pendiente.
- Actualizar las posibles asociaciones, las métricas y la visualización, y registrar la acción para permitir deshacerla.

Si el identificador ya existe o algún dato es inválido, no se modifica ninguna estructura y se informa la causa.

## Consulta de un evento

El usuario podrá localizar un evento mediante su identificador, aunque su prioridad o magnitud hayan cambiado desde la creación. El resultado debe indicar si está activo, archivado o eliminado. Para un evento activo se muestran sus datos vigentes, revisión, estaciones con reportes aceptados, pertenencia a zona poblada, prioridad, clave, estado de atención, profundidad del nodo, altura, factor de balance y asociaciones.

El identificador es solo el tercer componente de la clave del AVL. El equipo debe decidir cómo localizarlo eficientemente y justificar la estructura auxiliar o estrategia elegida, junto con sus costos de tiempo y memoria.

## Corrección manual de un evento

Una corrección reemplaza uno o varios datos de un evento activo. El identificador es inmutable. Si la revisión vigente es r, la corrección manual produce automáticamente la revisión r + 1, incluso cuando la nueva clave resulte igual a la anterior.

La corrección completa se ejecuta como una sola acción:

- Conservar el estado anterior y validar todos los datos resultantes antes de aplicar cambios.
- Retirar el nodo usando la clave anterior cuando sea necesario, actualizar los datos, recalcular la pertenencia a zona poblada, la prioridad y la nueva clave, y reinsertar el evento.
- Marcar el evento como pendiente, recalcular las asociaciones afectadas y actualizar métricas y visualización.

Si la nueva clave es igual a la anterior, el equipo puede evitar una eliminación y reinserción innecesarias, siempre que conserve la revisión y demuestre que el orden sigue siendo válido. Si algún dato es inválido, no se aplica ninguna parte de la corrección.

## Estado de atención

Todo evento activo tiene estado pendiente o revisado. Las creaciones y las correcciones aceptadas lo dejan pendiente. El usuario puede marcarlo como revisado después de examinar su información vigente. Este cambio no modifica P, M ni I y, por tanto, no cambia la clave ni requiere reinsertar el nodo. Debe registrarse como una acción que pueda deshacerse. Una corrección posterior devuelve el evento a pendiente.

## Eliminación individual

La eliminación individual retira únicamente el evento seleccionado. Los demás nodos deben permanecer activos, incluidos los que eran descendientes de ese nodo antes de la operación. El sistema muestra previamente el evento afectado y, al ejecutar la acción, lo retira con el procedimiento de eliminación del AVL, actualiza las asociaciones que lo utilizaban como referencia, registra su identificador como eliminado y actualiza métricas y visualización.

# 7 Diferencia entre eliminación y archivo

Eliminar individualmente un nodo afecta solo a ese evento. Archivar un subárbol afecta a la raíz seleccionada por las reglas de archivo y a todos los nodos que pertenezcan a esa rama al comenzar la operación. Los eventos archivados salen del AVL activo, pero conservan su identidad, sus datos y sus asociaciones en el histórico.

Por ejemplo, si SIS-000120 tiene como descendientes a SIS-000115, SIS-000118 y SIS-000130, la eliminación individual de SIS-000120 retira solamente ese evento. El archivo de la rama con raíz SIS-000120 traslada los cuatro eventos al histórico. El conjunto que se archivará se fija antes de modificar el árbol y no cambia por las rotaciones realizadas durante la operación.

La eliminación individual y el archivo de una rama se registran como acciones únicas que pueden deshacerse, aunque internamente requieran varias modificaciones o rotaciones.

## Procesamiento de reportes recibidos

Cada reporte contiene los datos completos del evento, su identificador, un número de revisión y la estación emisora. La numeración de revisión es global para ese evento, no independiente por estación. Para este proyecto, reportes con identificadores distintos representan terremotos distintos; no se exige deduplicación por proximidad.

| Situación del reporte | Resultado obligatorio |
|---|---|
| **Identificador desconocido** | Registrar un evento nuevo si los datos son válidos. La primera revisión recibida puede ser mayor que 1. |
| **Revisión mayor que la vigente** | Sustituir los datos vigentes, recalcular prioridad y asociaciones y ajustar la ubicación en el árbol si cambió la clave. |
| **Igual revisión e iguales datos** | Confirmar el evento y añadir la estación si aún no figuraba. Repetir la misma confirmación no crea nodos ni duplica estaciones. |
| **Igual revisión y datos distintos** | Informar un conflicto y rechazar el reporte sin sobrescribir los datos del evento. |
| **Revisión menor que la vigente** | Informar que el reporte es antiguo y descartarlo sin modificar el evento. |

La igualdad de datos se refiere a magnitud, profundidad, epicentro y tiempo de ocurrencia; no al emisor del reporte ni al formato del texto. El equipo debe representar las cantidades de modo que las comparaciones sean consistentes.

Un evento archivado conserva su identidad. Una revisión mayor y válida lo reactiva como pendiente en el AVL con sus datos corregidos. Una confirmación o un reporte antiguo no lo reactiva. Un identificador eliminado se conserva como retirado: sus reportes posteriores se rechazan hasta deshacer esa eliminación.

# 8 Asociaciones entre eventos

Un evento A es candidato a referencia de B cuando tiene mayor magnitud, ocurrió estrictamente antes y cumple ambas condiciones: la diferencia temporal es como máximo W horas y la distancia entre epicentros es como máximo R km. Se usa distancia euclidiana en el plano del escenario. Los valores iniciales son W = 48 horas y R = 40 km; ambos son positivos y modificables por el usuario.

Se consideran eventos activos y archivados, pero no eliminados. B debe mostrar sus candidatos y, si existe alguno, asociarse con uno como posible réplica. Si no hay candidatos, queda sin asociación. Cuando hay varios, el equipo define y sustenta un criterio determinista que dependa de los datos, no del orden de llegada ni de la topología del AVL.

Un alta, una corrección, una eliminación o un cambio de W o R debe actualizar las asociaciones afectadas. Una rotación o un simple archivo no cambia esas relaciones. Las referencias deben utilizar identidades válidas y no producir ciclos. No se exige identificar un sismo principal definitivo ni predecir eventos futuros.

# 9 Recepción mediante cola y modo estrés

## Ráfagas de reportes

El usuario podrá preparar reportes de N estaciones, con N ≥ 1, sin aplicarlos inmediatamente. Todos ingresan a una cola FIFO, cuyo orden de recepción será visible. El sistema ofrece procesamiento de un reporte por paso y procesamiento continuo con pausa entre pasos.

Los reportes de cada paso se resuelven completamente antes del siguiente. Se debe mostrar la estación, el evento, la revisión, la decisión tomada y las rotaciones producidas. Se simulan fuentes concurrentes; no se exige usar hilos ni modificar el árbol simultáneamente.

La cola conserva el orden de recepción. La prioridad de un terremoto determina su posición en el AVL, no su posición en la cola. Deben incluirse ráfagas con altas, confirmaciones, reportes antiguos y correcciones que cambian la clave.

## Balanceo diferido y recuperación

En modo normal, las inserciones, correcciones y eliminaciones finalizan con un árbol AVL válido. En modo estrés se realizan las mismas operaciones conservando el orden BST, pero se aplazan las rotaciones. Durante este modo la estructura puede dejar de cumplir la condición AVL y la interfaz debe indicarlo.

Al solicitar la recuperación global, se pausa el procesamiento de reportes. El sistema detecta los desbalances y aplica las rotaciones necesarias hasta restablecer la propiedad AVL. Se muestran los cambios y su costo. No se permite vaciar el árbol para sustituirlo por otro construido a partir de una lista ordenada.

El equipo debe diseñar una recuperación válida aun cuando existan diferencias de altura mayores que 2. Debe sustentar por qué su procedimiento termina y preserva el orden. El retorno al modo normal solo se completa cuando la auditoría confirma el equilibrio.

# 10 Profundidad del nodo y presupuesto de acceso

La profundidad de la raíz es 0 y la de un hijo es la de su padre más 1. El usuario configura un límite L entero no negativo, inicialmente 3, antes de cargar los datos o durante la ejecución. Un evento activo de prioridad alta se marca con acceso costoso cuando su profundidad en el árbol es estrictamente mayor que L.

La marca se actualiza después de toda operación que cambie datos, estructura o límite. Se debe permitir distinguir visualmente la prioridad del evento y la marca de acceso costoso sin confundirlas.

El costo simulado de localizar un evento por su clave es el número de nodos visitados desde la raíz; para un evento existente equivale a su profundidad más 1. Esta medición no representa tiempo real. La profundidad del hipocentro se expresa en kilómetros y es un dato diferente de la profundidad del nodo.

La marca de acceso costoso no modifica P, M ni I. Por tanto, una rotación puede cambiar esa marca sin producir por sí misma una corrección del terremoto ni un cambio de clave.

# 11 Eliminación individual y archivo de subárboles

La eliminación individual retira solamente el evento seleccionado. Sus descendientes permanecen en el catálogo y el árbol se reorganiza según el modo activo. Se actualizan las asociaciones que lo utilizaban como referencia y se conserva su identificador como retirado.

## Selección de una rama para archivo

La operación **Archivar rama de eventos antiguos** evalúa los subárboles del AVL activo. Un subárbol es elegible si todos sus eventos tienen prioridad baja y antigüedad estrictamente mayor que T horas. La antigüedad se calcula entre el reloj de simulación y la hora de ocurrencia. T es positivo, configurable y vale inicialmente 72 horas.

Entre las ramas elegibles se elige la de mayor cantidad de nodos. Si hay empate, se elige aquella cuya raíz tenga mayor profundidad en el árbol; si persiste, la de mayor identificador numérico de su raíz. Una hoja también es un subárbol. Si todo el árbol es elegible, se permite archivarlo completo.

Antes de ejecutar, se muestran los identificadores afectados, su cantidad y la justificación de la selección. El conjunto corresponde a la topología existente al iniciar la operación y se mantiene fijo durante su ejecución. Las rotaciones intermedias no pueden añadir ni excluir eventos de ese conjunto.

Los eventos pasan al histórico y dejan de estar en el AVL activo. El histórico conserva sus datos e identidades para consultas y asociaciones. En modo normal se restablece el balance; en estrés se mantiene solo el orden. La operación completa se deshace con una única acción. Si no existe una rama elegible, se informa y se conserva el estado.

# 12 Consultas y análisis del desempeño

El sistema ofrecerá las siguientes consultas sobre eventos activos, salvo la consulta de asociaciones, que también considera el histórico:

- Los primeros k eventos pendientes de atención en orden descendente de K. k es entero positivo; si hay menos pendientes, se muestran todos los disponibles. Marcar un evento revisado no cambia su clave.
- Eventos dentro de un intervalo inclusivo de magnitud, y eventos con profundidad del hipocentro menor o igual a un límite dentro de un intervalo inclusivo de fechas.
- Candidatos y referencia elegida para un evento, así como los eventos que lo utilizan como referencia. Se identifica si cada resultado está activo o archivado.
- Eventos de prioridad alta con acceso costoso, indicando profundidad del nodo, límite y número de nodos visitados en su búsqueda por clave.

Cada consulta debe reportar la cantidad de nodos del AVL examinados. El equipo explicará qué ramas puede descartar con seguridad según K. No se presume que todas las consultas sean logarítmicas; deben analizar el costo en el peor caso y el de las estructuras auxiliares empleadas.

Para un mismo conjunto de eventos se probarán distintos órdenes de inserción, incluido un orden ascendente de claves. Se compararán AVL y BST mediante altura, hojas y comparaciones al buscar las mismas claves. Los tiempos medidos pueden añadirse, pero no sustituyen las métricas estructurales.

# 13 Persistencia y reconstrucción del escenario

El usuario seleccionará el archivo JSON mediante un explorador de archivos. No se permiten rutas de entrada fijas en el código. Deben existir los dos modos de carga que se describen a continuación.

## Carga por inserciones

El archivo contiene una secuencia de eventos con identificadores únicos. Se aplican exactamente el mismo comparador y orden de inserción a un AVL y a un BST sin balanceo. Esta carga se realiza con balanceo activo en el AVL. Al finalizar se muestran ambos árboles y sus raíces, alturas, profundidades máximas y cantidades de hojas.

Esta modalidad utiliza eventos, no reportes repetidos. Las confirmaciones y revisiones de un mismo identificador se evalúan mediante la cola. Un identificador duplicado en la secuencia de carga invalida el archivo.

## Carga por topología

El archivo describe explícitamente la raíz y los enlaces izquierdo y derecho de cada nodo. Se debe recuperar esa topología sin sustituirla por reinserciones. El equipo define el esquema JSON, incluyendo cómo representa enlaces vacíos e identidades.

Antes de sustituir el escenario actual se validan datos, unicidad, referencias, ausencia de ciclos, pertenencia de cada nodo activo a una sola posición, orden global BST, alturas y factores almacenados. Una prioridad almacenada debe coincidir con la calculada. Los eventos activos e históricos no pueden duplicar identidades.

Una topología ordenada y balanceada puede cargarse en modo normal. Una topología ordenada pero desbalanceada solo puede cargarse con el modo estrés activado y debe señalarse como tal. Un orden incorrecto, una referencia inválida o metadatos inconsistentes obligan a rechazar la carga. El programa muestra los problemas detectados y conserva el escenario anterior.

## Guardado estructural

La exportación debe permitir recuperar el mismo escenario operativo:

- Topología real del árbol activo, datos vigentes, alturas, factores de balance y estado de atención.
- Histórico, identificadores retirados, estaciones y asociaciones entre eventos.
- Cola en su orden original, reloj de simulación, zonas, parámetros W, R, L y T, modo de ejecución y métricas acumuladas del estado.

No basta con guardar la lista de eventos. Los valores derivados almacenados se verifican al cargar. El equipo puede guardar las asociaciones o reconstruirlas con su política determinista; en ambos casos debe recuperar el mismo resultado lógico.

La carga debe ser completa o no aplicarse. El esquema, las validaciones y los mensajes de error forman parte del diseño técnico que deberá sustentar el equipo. No se exige un formato JSON idéntico entre equipos.

# 14 Deshacer y versiones persistentes

La pila de retroceso debe permitir deshacer acciones sucesivas y recuperar el estado anterior exacto, incluida la topología. Cada alta, corrección, eliminación, archivo masivo, cambio de parámetros, avance del reloj, cambio de atención, carga y recuperación global constituye una acción independiente.

Cada paso de procesamiento de la cola también constituye una acción. Al deshacerlo se restablecen tanto el escenario como la posición del reporte en la cola, incluso si ese paso había descartado un reporte. Las inserciones y rotaciones internas de una corrección o archivo masivo no se deshacen por separado.

El estado recuperado incluye datos, histórico, referencias, cola, reloj, parámetros, modo y métricas. La representación del historial queda a cargo del equipo: deberá justificar su consumo de memoria y garantizar que cambios posteriores no alteren estados anteriores.

Además de deshacer, el usuario podrá guardar versiones con nombre y restaurarlas por selección. Las versiones persisten después de cerrar el programa e incluyen el mismo estado operativo definido para la exportación. No necesitan contener la pila de retroceso ni otras versiones. Restaurar una versión es una acción que puede deshacerse.

# 15 Auditoría e indicadores

La opción **Verificar estructura** estará disponible en ambos modos y generará un reporte por evento inconsistente. Debe comprobar el orden global por K, unicidad, referencias, alturas recalculadas y factores de balance. No basta con comprobar que cada hijo inmediato esté en el lado correcto.

Se adopta altura del árbol vacío igual a -1 y altura de una hoja igual a 0. El factor de balance de un nodo es altura izquierda menos altura derecha. En modo normal todos deben pertenecer a {-1, 0, 1}. En estrés se informa el desbalance esperado y se distinguen los errores de orden o de metadatos.

La interfaz mantendrá visibles o accesibles los siguientes indicadores:

- Cantidad de eventos activos e históricos, altura, hojas y recorridos inorden, preorden, postorden y por niveles.
- Correcciones aceptadas, reportes descartados, conflictos, archivos masivos y eventos archivados.
- Casos LL, RR, LR y RL atendidos, junto con giros simples a izquierda y derecha. Un caso doble cuenta como un caso LR o RL y dos giros elementales.
- Eventos por prioridad, pendientes de atención y eventos marcados con acceso costoso.

Los contadores forman parte del estado restaurable: deshacer o restaurar una versión recupera sus valores anteriores. El registro de una acción debe permitir explicar cómo se obtuvieron sus métricas.

# 16 Presentación de la solución

La aplicación tendrá una vista gráfica del AVL y una vista comparativa con el BST. El usuario podrá inspeccionar las claves y los enlaces, observar cambios de estructura y acceder a cola, histórico, versiones y auditoría. El equipo decide la distribución de pantallas y la técnica de dibujo. La interfaz debe comunicar qué operación ocurrió y por qué produjo ese resultado. Al igual se deberá tener una gráfica donde se observe el plano geográfico con los eventos representados como el equipo lo decida y lo sustente de manera que se interprete de manera fácil por el usuario final.

# 17 Casos mínimos para demostrar la solución

Cada equipo preparará datos reproducibles, declarará el estado inicial y mostrará resultados esperados y obtenidos. Los siguientes casos son obligatorios; pueden añadirse otros para sustentar el diseño.

- **Límites y empates.** Probar M = 4,5, M = 6,0, H = 30,0 km y un epicentro sobre el borde de una zona. Insertar eventos con igual prioridad y magnitud para evidenciar el desempate por identificador.
- **Corrección y reporte antiguo.** Corregir un evento de M = 4,8 y H = 70,0 km a M = 6,2 y H = 15,0 km. Su prioridad pasa de 2 a 3. Recibir después una revisión menor y demostrar que no se crea otro nodo ni se revierte la corrección.
- **Reporte tardío.** Recibir eventos cercanos de magnitudes 5,6 a las 10:00 y 4,2 a las 10:20. Recibir después uno de magnitud 6,1 ocurrido a las 09:55. Mostrar los candidatos nuevos y el resultado de la política de selección del equipo.
- **Rotaciones y recuperación.** Provocar los cuatro casos de balanceo. Generar una estructura degradada en estrés, repararla y demostrar que conserva identidades, orden y asociaciones. Incluir desbalances mayores que 2.
- **Archivo masivo.** Mostrar una rama elegible con varios eventos, los criterios de desempate y la situación sin ramas elegibles. Evidenciar que una rama cuya raíz sea de baja prioridad no es elegible si contiene un descendiente de prioridad mayor. Deshacer el archivo completo.
- **Persistencia y consistencia.** Guardar y recuperar una topología normal y otra en estrés. Rechazar un archivo inconsistente sin alterar el estado actual. Restaurar una versión después de reiniciar y deshacer una corrección y un paso de cola.

# 18 Entregables y sustentación

- Código en un repositorio Git que permita evidenciar los aportes de cada integrante, instrucciones de ejecución y comentarios de código en inglés.
- Manual de usuario y manual técnico. El técnico debe incluir modelo de dominio, responsabilidades, esquema JSON, invariantes, decisiones abiertas resueltas y análisis de costos de tiempo y memoria, al igual que un reporte del uso de IA en el desarrollo del proyecto. Estos documentos deberán estar adjuntos al correo electrónico y **NO compartidos en Dropbox, Drive, Git, etc.**
- Archivos de prueba de ambos modos de carga, ráfagas de reportes y evidencia de los casos de la sección 16. Incluir pruebas de inserción, eliminación, corrección, recuperación e integridad del AVL.
- Video de explicación de la solución y su arquitectura en un segundo idioma, con participación visible de todos los integrantes en primer plano, y por otra parte un videotutorial del sistema en ejecución.

La evaluación se distribuye en 50 % para funcionalidad en equipo y 50 % para sustentación individual. En la sustentación, cada integrante deberá explicar la comparación de claves, justificar una decisión de diseño y analizar los efectos de una operación sobre el árbol y las demás estructuras, además de realizar modificaciones en código si así se solicita. En caso de obtener una calificación individual muy por debajo de la grupal, se hará un reajuste de la nota grupal con base en la individual.

La fecha de entrega será el **7 de octubre**. El repositorio y los materiales deben corresponder a la versión presentada.
