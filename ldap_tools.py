from ldap3 import Server, Connection, ALL, SUBTREE 

LDAP_URL = "ldap://localhost:389" 
BASE_DN_USERS = "ou=users,dc=meli,dc=com" 
BASE_DN_GROUPS = "ou=groups,dc=meli,dc=com" 
ADMIN_DN = "cn=admin,dc=meli,dc=com" 
ADMIN_PASS = "itachi" 

def connect(): 
    server = Server(LDAP_URL, get_info=ALL) 
    conn = Connection(server, user=ADMIN_DN, password=ADMIN_PASS, auto_bind=True) 
    return conn 
    
def get_current_user_info() -> dict: 
    conn = connect() 
    conn.search(BASE_DN_USERS, "(cn=test.user)", SUBTREE, attributes=["cn","uid","mail"]) 
    if not conn.entries: 
        return {} 
    entry = conn.entries[0] 
    return { 
        "dn": entry.entry_dn, 
        "cn": str(entry.cn) if "cn" in entry else None, 
        "uid": str(entry.uid) if "uid" in entry else None, 
        "mail": str(entry.mail) if "mail" in entry else []  
        } 
        
def get_user_groups(username: str): 
    try: 
        server = Server(LDAP_URL, get_info=ALL) 
        conn = Connection(server, ADMIN_DN, ADMIN_PASS, auto_bind=True) 
        
        conn.search(
            search_base=BASE_DN_GROUPS, 
            search_filter="(objectClass=groupOfNames)", 
            attributes=["cn", "member"]
        ) 
        
        user_dn = f"cn={username},{BASE_DN_USERS}" 
        user_groups = [] 
        
        for entry in conn.entries: 
            members = entry.member.values if "member" in entry else [] 
            if user_dn in members: 
                user_groups.append(entry.cn.value) 
            
        conn.unbind() 
        return user_groups 
        
    except Exception as e: 
        return f"Error LDAP: {e}"

def list_all_users():
    try:
        conn = connect()
        conn.search(BASE_DN_USERS, "(objectClass=inetOrgPerson)", SUBTREE, attributes=["cn", "uid", "mail"])
        users = []
        for entry in conn.entries:
            users.append({
                "cn": str(entry.cn) if "cn" in entry else "",
                "uid": str(entry.uid) if "uid" in entry else "",
                "mail": str(entry.mail) if "mail" in entry else ""
            })
        conn.unbind()
        return users
    except Exception as e:
        return f"Error LDAP: {e}"
        
def list_all_groups():
    try:
        conn = connect()
        conn.search(BASE_DN_GROUPS, "(objectClass=groupOfNames)", SUBTREE, attributes=["cn"])
        groups = [str(entry.cn) for entry in conn.entries]
        conn.unbind()
        return groups
    except Exception as e:
        return f"Error LDAP: {e}"
        
def search_privileged_accounts():
    try:
        keywords = ["admin", "root", "it", "developers", "backup", "security"]

        conn = connect()
        filtro = "(|" + "".join([f"(cn=*{kw}*)" for kw in keywords]) + ")"
        conn.search(BASE_DN_GROUPS, filtro, SUBTREE, attributes=["cn", "member"])

        usuarios = []
        for grupo in conn.entries:
            if "member" in grupo:
                usuarios.extend(grupo.member.values)

        conn.unbind()
        return usuarios

    except Exception as e:
        return f"Error LDAP: {e}"
