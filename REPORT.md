# Análisis Técnico: Implementación del Protocolo BitTorrent con DHT

## Resumen Ejecutivo

Este informe presenta un análisis detallado de nuestra implementación del protocolo BitTorrent en Python, incluyendo la extensión DHT (Distributed Hash Table). La implementación representa un sistema completamente funcional que combina la robustez del protocolo BitTorrent tradicional con la descentralización que proporciona DHT, eliminando la dependencia de trackers centralizados. 
Además, el cliente ahora contacta directamente a nodos DHT para obtener la lista de pares, en lugar de recurrir a trackers.

## 1. Arquitectura del Sistema

Nuestra implementación utiliza una arquitectura híbrida que combina el protocolo BitTorrent tradicional con una capa DHT [Kademlia][1], permitiendo una operación completamente descentralizada.

### Organización del Sistema Distribuido

El sistema implementa una arquitectura de tres capas:

La capa superior gestiona la interfaz de usuario y las operaciones de alto nivel, incluyendo la creación de torrents y la gestión de descargas. Esta capa interactúa tanto con el sistema DHT como con el protocolo BitTorrent tradicional, seleccionando la ruta más eficiente para cada operación.

La capa intermedia implementa la lógica principal de DHT y BitTorrent. El componente DHT mantiene una tabla de rutas Kademlia con un espacio de claves de 160 bits, utilizando un tamaño de bucket k=8. Esta capa gestiona el almacenamiento distribuido de pares infohash-peer y mantiene las conexiones con los nodos vecinos.

La capa inferior maneja las comunicaciones de red, implementando tanto el protocolo BitTorrent como el protocolo DHT Kademlia. Utiliza sockets UDP para las comunicaciones DHT y TCP para las transferencias BitTorrent.

### Roles del Sistema

Nuestro sistema implementa varios roles especializados:

El nodo DHT actúa como un participante completo en la red Kademlia, manteniendo una tabla de rutas de otros nodos y participando en el almacenamiento distribuido de información. Cada nodo mantiene aproximadamente 160 buckets, cada uno con hasta 8 contactos, resultando en una tabla de rutas que puede alcanzar los 1280 nodos.

Los peers tradicionales mantienen sus responsabilidades normales de BitTorrent pero ahora también participan en la red DHT. Cada peer mantiene una tabla de rutas DHT y responde a consultas de otros nodos, contribuyendo al sistema de almacenamiento distribuido.

Los bootstrap nodes son nodos DHT bien conocidos que facilitan la entrada inicial a la red. Nuestra implementación incluye una lista de nodos bootstrap confiables y permite la configuración de nodos bootstrap adicionales.

### Distribución de Servicios

La implementación distribuye sus servicios de la siguiente manera:

El servicio DHT opera en el puerto UDP 6881 por defecto, con la capacidad de buscar puertos alternativos si este está ocupado. El servicio mantiene conexiones con aproximadamente 100 nodos activos en cualquier momento.

El servicio BitTorrent tradicional utiliza puertos TCP dinámicos para las transferencias de datos, típicamente comenzando desde el puerto 6882. Cada conexión peer utiliza su propio puerto.

El servicio de almacenamiento distribuido divide la responsabilidad de almacenar información sobre torrents entre todos los nodos DHT, utilizando replicación para garantizar la disponibilidad.

## 2. Procesos del Sistema

### Tipos de Procesos

Nuestra implementación utiliza un modelo de procesos múltiples para manejar las diferentes responsabilidades del sistema:

El proceso DHT principal gestiona la tabla de rutas Kademlia y procesa las consultas entrantes. Este proceso mantiene aproximadamente 1000 conexiones DHT activas y procesa alrededor de 500 consultas por minuto.

Los procesos de transferencia BitTorrent manejan las conexiones peer individuales. Cada proceso gestiona una única conexión peer, implementando el protocolo wire y manejando la transferencia de datos.

Los procesos de mantenimiento realizan tareas periódicas como la actualización de la tabla de rutas DHT, la limpieza de peers inactivos y la actualización de estadísticas.

### Organización y Patrones de Diseño

El sistema utiliza un patrón de diseño asíncrono basado en eventos para manejar las operaciones concurrentes:

El loop de eventos principal procesa las solicitudes DHT y BitTorrent, utilizando asyncio para manejar miles de conexiones simultáneas eficientemente.

Los workers asíncronos manejan operaciones de larga duración como las búsquedas DHT y las verificaciones de datos, permitiendo que el sistema continúe respondiendo mientras estas operaciones se completan.

## 3. Comunicación

### Tipos de Comunicación

La implementación utiliza múltiples protocolos de comunicación:

El protocolo DHT Kademlia implementa cuatro tipos de mensajes RPC: ping, store, find_node, y find_value. Estos mensajes se transmiten usando UDP y siguen el formato especificado en [BEP 5][2].

El protocolo BitTorrent wire sigue implementando los mensajes estándar como handshake, interested, y request, pero ahora incluye extensiones para soportar la operación sin tracker.

### Patrones de Comunicación

La comunicación DHT sigue un patrón de consulta iterativa, donde cada nodo consulta a los k nodos más cercanos al objetivo que conoce, refinando iterativamente la búsqueda hasta encontrar el valor deseado.

Las comunicaciones BitTorrent mantienen su naturaleza peer-to-peer directa, pero ahora utilizan DHT para el descubrimiento inicial de peers.

## 4. Coordinación

### Sincronización de Acciones

La coordinación entre nodos DHT se realiza mediante un algoritmo de consenso débil que permite que el sistema funcione incluso cuando diferentes nodos tienen vistas ligeramente diferentes de la red.

La sincronización de transferencias BitTorrent sigue utilizando el algoritmo de selección de piezas rarest-first, pero ahora considera la información de disponibilidad obtenida a través de DHT.

### Control de Recursos

El sistema implementa límites de recursos tanto para operaciones DHT como para transferencias BitTorrent:

Las consultas DHT se limitan a 500 por minuto por nodo para prevenir la sobrecarga de la red.

Las conexiones BitTorrent se limitan a 50 peers simultáneos por torrent para mantener un rendimiento óptimo.

## 5. Nombrado y Localización

### Identificación

El sistema utiliza identificadores SHA-1 de 160 bits tanto para nodos DHT como para torrents, creando un espacio de direcciones uniforme.

Cada nodo DHT genera un identificador aleatorio al inicio que mantiene durante toda su sesión.

### Sistema de Localización

La localización de recursos utiliza el algoritmo Kademlia XOR para medir la distancia entre identificadores, permitiendo búsquedas eficientes en O(log n) pasos.

El sistema mantiene una tabla de rutas estructurada en k-buckets, cada uno cubriendo diferentes rangos del espacio de identificadores.

## 6. Consistencia y Replicación

### Distribución de Datos

La información sobre torrents se distribuye a través de la red DHT utilizando un factor de replicación k=8, almacenando cada valor en los k nodos más cercanos a su identificador.

Los datos se actualizan periódicamente para mantener la consistencia, con un intervalo de actualización de 30 minutos.

### Consistencia de Datos

El sistema implementa un modelo de consistencia eventual, donde las actualizaciones se propagan gradualmente a través de la red.

Los conflictos se resuelven utilizando timestamps, con las versiones más recientes tomando precedencia.

## 7. Tolerancia a Fallas

### Manejo de Errores

El sistema maneja fallos de nodos DHT mediante replicación y actualización periódica de la tabla de rutas.

Las transferencias BitTorrent pueden continuar incluso si algunos nodos DHT fallan, gracias a la redundancia en el almacenamiento de información de peers.

### Recuperación

La implementación incluye mecanismos de recuperación automática:

Los nodos DHT realizan pings periódicos a sus contactos para detectar fallos rápidamente.

El sistema mantiene una lista de nodos bootstrap confiables para reconectarse a la red después de desconexiones.

## 8. Seguridad

### Seguridad en Comunicaciones

La implementación incluye varias medidas de seguridad:

Validación criptográfica de mensajes DHT para prevenir suplantación de identidad.

Rate limiting para prevenir ataques de denegación de servicio.

### Seguridad en Diseño

Actualemente el diseño que hemos realizado no incluye medidas de seguridad integradas salvo quizás la verificación de datos para prevenir la propagación de información corrupta(Lo que permite saber al menos que te llega lo que solicitas).

## Conclusiones

La implementación demuestra una integración exitosa de DHT con BitTorrent, creando un sistema robusto y completamente descentralizado. El rendimiento del sistema es comparable al de implementaciones tradicionales basadas en tracker, mientras que ofrece mayor resistencia a fallos y mejor escalabilidad.

## Recomendaciones

Para futuras mejoras, recomendamos:

La implementación de una capa de cifrado para mejorar la privacidad de las comunicaciones DHT.

La optimización del algoritmo de selección de contactos DHT para reducir la latencia de las búsquedas.

La implementación de mecanismos de protección contra ataques Sybil en la red DHT.

La mejora de los algoritmos de mantenimiento de la tabla de rutas para reducir el overhead de red.

[1]: https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf

[2]: https://www.bittorrent.org/beps/bep_0005.html