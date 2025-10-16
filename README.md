# 🧠 Agente LDAP con LLM (Gemini + LangChain)

Este proyecto implementa un **agente conversacional** capaz de consultar un servidor **LDAP** utilizando un **modelo de lenguaje Gemini** a través de **LangChain**.
Permite obtener información de usuarios y los grupos a los que pertenecen mediante consultas en lenguaje natural.
Permite también enumerar los usuarios y grupos existentes en un dominio, además de obtener los usuarios que podrían tener privilegios elevados.
Adicionalmente, tiene capacidad de auto-expansión, permitiendo la generación de nuevas herramientas automáticamente a partir de la consulta realizada.

---

## 🚀 Características

* Conexión a **OpenLDAP** usando la librería `ldap3`.
* Consultas dinámicas sobre:
  
  * Información del usuario actual.
  * Grupos a los que pertenece un usuario específico.
  * Enumeración de usuarios
  * Enumeración de grupos
  * Búsqueda de posibles cuentas con privilegios elevados
* Integración con **Google Gemini** a través de `langchain-google-genai`.
* Interfaz interactiva desde consola.
* Generación automática de nuevas herramientas

---

## 🧬 Estructura del proyecto

```
.
├── ldap_tools.py        # Funciones para interactuar con el servidor LDAP
├── generated_tools.py   # Funciones auto-generadas por el agente
├── main.py              # Inicializa el agente y maneja el loop de conversación
├── pyproject.toml       # Dependencias del proyecto (Poetry)
└── README.md            # Este archivo
```

---

## ⚙️ Requisitos

* Python **3.12+**
* [Poetry](https://python-poetry.org/docs/#installation)
* Clave API de **Google Gemini**

---

## 🔧 Instalación

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/mauricio-chiabrando/meli_offsec_challenge_extra.git
   cd meli_offsec_challenge_extra
   ```

2. Instalar dependencias con **Poetry**:

   ```bash
   poetry install
   poetry shell
   ```

3. Exportar tu clave de **Gemini**:

   ```bash
   export GOOGLE_API_KEY="TU_API_KEY_DE_GEMINI"
   ```

---

## ▶️ Uso

Debido a que el usuario que ejecuta el agente no está en el servidor LDAP provisto, el usuario por el cual se consulta se deberá definir directamente en el archivo ldap_tools.py:

```bash
conn.search(BASE_DN_USERS, "(cn=USUARIO_DE_LDAP)", SUBTREE, attributes=["cn","uid","mail"]) 
```

Ejecutar el agente desde la terminal:

```bash
python3 main.py
```

Luego podés escribir consultas naturales como:

```
>> ¿Quién soy?
>> ¿A qué grupos pertenezco?
>> ¿Qué grupos tiene el usuario john.doe?
>> ¿Cuales son los usuarios del dominio?
>> ¿Qué grupos existen en el dominio?
>> ¿Qué usuarios podrían tener privilegios elevados?
```

En caso que la consulta no se pueda ejecutar debido a que las herramientas incluidas no lo permitan, el agente generará automáticamente nuevas funciones en el archivo "generated_tools.py".
Las herramientas auto-generadas serán eliminadas al salir del agente, dejando solo las funciones originales.
Por ejemplo:

```
>> ¿Existen grupos vacíos?
```

Para salir:

```
exit
```

---

## 🧠 Funcionamiento interno

El agente utiliza **LangChain** con un modelo **Gemini 2.5 Flash**.
Se le asignan cinco herramientas principales:

| Herramienta                  | Descripción                                                                      |
| ---------------------------- | -------------------------------------------------------------------------------- |
| `get_current_user_info`      | Devuelve la información del usuario autenticado en LDAP                          |
| `get_user_groups`            | Devuelve los grupos a los que pertenece un usuario específico                    |
| `list_all_users`             | Enumera todos los usuarios visibles en el dominio                                |
| `list_all_groups`            | Lista todos los grupos disponibles en LDAP                                       |
| `search_privileged_accounts` | Busca cuentas sensibles, privilegiadas, con altos permisos o de servicio comunes |

Ejemplo de configuración del modelo:

```python
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY")
)
```

---

## 🧪 Ejemplo de salida

```
Agente de consulta LDAP con LLM iniciado. Podés escribir en lenguaje natural (exit para salir).

>> ¿Quién soy?
Eres el usuario con cn 'test.user', uid 'test.user', y tu correo es 'test.user@meli.com'.

>> ¿A qué grupos pertenezco?
Perteneces a los grupos: qa, all_users.

>> ¿Cuales son los usuarios del dominio?
Los usuarios del dominio son: admin, john.doe, jane.smith, bob.wilson, alice.brown, test.user, carlos.rodriguez.

>> ¿Qué grupos existen en el dominio?
Los grupos existentes en el dominio son: admins, developers, managers, hr, finance, qa, it, all_users.

>> ¿Qué usuarios podrían tener privilegios elevados?
Los usuarios que podrían tener privilegios elevados son: cn=admin,ou=users,dc=meli,dc=com, cn=john.doe,ou=users,dc=meli,dc=com, cn=jane.smith,ou=users,dc=meli,dc=com.

(EXTRA)
>> ¿Existen grupos vacíos?
No, no existen grupos vacíos. Todos los grupos listados ('admins', 'developers', 'managers', 'hr', 'finance', 'qa', 'it', 'all_users') tienen al menos un miembro.
```

---

## 👨‍💻 Autor

**Mauricio Chiabrando**

💼 Challenge Técnico Offensive Security - Mercado Libre

📧 Contacto: [[mauricio.chiabrando@gmail.com](mailto:mauricio.chiabrando@gmail.com)]

---
