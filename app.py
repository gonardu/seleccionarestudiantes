# ---------- LOGIN ----------
st.title("🔒 Login")

# Inicializar variables de sesión
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    username_input = st.text_input("Usuario")
    password_input = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if check_password(username_input, password_input):
            st.success(f"Bienvenido, {username_input}!")
            st.session_state.logged_in = True
            st.session_state.username = username_input
        else:
            st.error("Usuario o contraseña incorrectos ❌")
else:
    username = st.session_state.username
    users = load_users()
    user_data = users[username]

    # ---------- Lista de alumnos ----------
    alumnos = st.text_area(
        "Lista de alumnos (uno por línea)",
        "\n".join(user_data["alumnos"])
    ).splitlines()
    if st.button("Guardar lista"):
        users[username]["alumnos"] = alumnos
        save_users(users)
        st.success("Lista guardada ✅")

    # ---------- Selección aleatoria con interfaz gráfica ----------
    st.markdown("### 🎯 Selección de alumno")
    if "seleccionado" not in st.session_state:
        st.session_state.seleccionado = None

    if st.button("Seleccionar alumno"):
        if alumnos:
            st.session_state.seleccionado = random.choice(alumnos)

    elegido = st.session_state.seleccionado or "ninguno"
    st.markdown(f"""
        <div style='border: 2px solid #4CAF50; border-radius: 10px; padding: 20px; margin-top: 10px; background-color:#f0f0f0; text-align:center; font-size:20px;'>
            Estudiante elegido: <strong>{elegido}</strong>
        </div>
    """, unsafe_allow_html=True)

    # ---------- Mostrar todos los alumnos ----------
    st.markdown("### 👩‍🎓 Lista de alumnos")
    for est in alumnos:
        st.markdown(f"""
            <div style='border: 1px solid #888; border-radius: 5px; padding: 10px; margin: 5px; background-color:#fafafa;'>
                {est}
            </div>
        """, unsafe_allow_html=True)

    # ---------- Guardar resultados en Excel ----------
    if "EXCEL_FILE" not in st.session_state:
        st.session_state.EXCEL_FILE = f"{username}_asistencia.xlsx"

    EXCEL_FILE = st.session_state.EXCEL_FILE

    # Inicializar Excel si no existe
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.cell(row=1, column=1, value="Nombre")
        for i, est in enumerate(alumnos, start=2):
            ws.cell(row=i, column=1, value=est)
        wb.save(EXCEL_FILE)

    wb = load_workbook(EXCEL_FILE)
    ws = wb.active

    def guardar_resultado(valor):
        fecha = datetime.today().strftime("%Y-%m-%d")
        col_fecha = None
        for col in range(2, ws.max_column + 1):
            if ws.cell(row=1, column=col).value == fecha:
                col_fecha = col
                break
        if not col_fecha:
            col_fecha = ws.max_column + 1
            ws.cell(row=1, column=col_fecha, value=fecha)
        for i in range(2, ws.max_row + 1):
            if ws.cell(row=i, column=1).value == st.session_state.seleccionado:
                ws.cell(row=i, column=col_fecha, value=valor)
                break
        wb.save(EXCEL_FILE)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Entregado"):
            if st.session_state.seleccionado:
                guardar_resultado("E")
                st.success("Guardado como ENTREGADO ✅")
    with col2:
        if st.button("❌ No entregado"):
            if st.session_state.seleccionado:
                guardar_resultado("X")
                st.error("Guardado como NO ENTREGADO ❌")
