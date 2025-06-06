document.addEventListener("DOMContentLoaded", () => {
  const tipoBusqueda = document.getElementById("tipo-busqueda");
  const busquedaInput = document.getElementById("busqueda-input");
  const inputBusqueda = document.getElementById("input-busqueda");
  const btnBuscar = document.getElementById("btn-buscar"); // Corregido: querySelectorById -> getElementById
  const resultados = document.getElementById("resultados"); // Corregido: resultado -> resultados
  const modalContainer = document.getElementById("modal-container");

  // Cargar template de tarjeta
  let tarjetaTemplate = '';
  fetch('/components/tarjeta_usuario.html')
    .then(res => {
      if (!res.ok) throw new Error('No se pudo cargar tarjeta_usuario.html');
      return res.text();
    })
    .then(data => {
      tarjetaTemplate = data;
    })
    .catch(error => console.error('Error cargando tarjeta_usuario.html:', error));

  // Cargar template de modal
  fetch('/components/modal_detalle.html')
    .then(res => {
      if (!res.ok) throw new Error('No se pudo cargar modal_detalle.html');
      return res.text();
    })
    .then(data => {
      modalContainer.innerHTML = data;
      // Agregar event listeners después de cargar el modal
      const cerrarModalBtn = document.getElementById("cerrar-modal");
      if (cerrarModalBtn) {
        cerrarModalBtn.addEventListener("click", cerrarModal);
      } else {
        console.error('Elemento con id "cerrar-modal" no encontrado');
      }

      window.addEventListener("click", (e) => { // Corregido: comilla simple -> comilla doble
        const modal = document.getElementById("modal-detalle");
        if (modal && e.target === modal) {
          cerrarModal();
        }
      });
    })
    .catch(error => {
      console.error('Error cargando modal_detalle.html:', error);
      modalContainer.innerHTML = '<p>Error al cargar el modal</p>';
    });

  // Mostrar/esconder input según el tipo de búsqueda
  tipoBusqueda.addEventListener("change", () => {
    if (tipoBusqueda.value === "placa" || tipoBusqueda.value === "persona") {
      busquedaInput.classList.remove("hidden");
      inputBusqueda.focus();
    } else {
      busquedaInput.classList.add("hidden");
      inputBusqueda.value = ''; // Limpiar input
      if (tipoBusqueda.value === "deudores" || tipoBusqueda.value === "aldia") {
        buscar();
      }
    }
  });

  // Función para realizar la búsqueda
  async function buscar() {
    const tipo = tipoBusqueda.value;
    let query = inputBusqueda.value.trim();

    if (!tipo) {
      resultados.innerHTML = '<p class="text-red-500">Seleccione un tipo de búsqueda</p>';
      return;
    }

    if ((tipo === 'placa' || tipo === 'persona') && !query) {
      resultados.innerHTML = '<p class="text-red-500">Ingrese un valor para buscar</p>'; // Corregido: falta de comilla de cierre
      return;
    }

    resultados.innerHTML = "<p>Cargando...</p>";

    try {
      const params = new URLSearchParams({ tipo });
      if (tipo === 'placa' || tipo === 'persona') {
        // Normalizar query: eliminar espacios y convertir a mayúsculas para placas
        query = query.replace(/\s+/g, '');
        params.append("query", tipo === 'placa' ? query.toUpperCase() : query);
      }

      const res = await fetch(`/buscar?${params.toString()}`);
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ error: 'Error desconocido' }));
        throw new Error(errorData.error || `Error ${res.status}`);
      }

      const data = await res.json();

      if (data.error) {
        resultados.innerHTML = `<p class="text-red-500">${data.error}</p>`;
        return;
      }

      if (data.length === 0) {
        resultados.innerHTML = '<p class="text-gray-500">No se encontraron resultados</p>';
        return;
      }

      resultados.innerHTML = '';
      data.forEach(item => {
        const tarjetaHtml = tarjetaTemplate
          .replace('{{ placa }}', item.placa)
          .replace('{{ nombre }}', item.nombre)
          .replace('{{ estadoPago }}', item.estado)
          .replace('{{ id_propietario }}', item.propietario_id)
          .replace('{{ estadoClase }}', item.estado === 'en mora' ? 'mora' : 'aldia'); // Nueva línea para reemplazar estadoClase

        const div = document.createElement('div');
        div.innerHTML = tarjetaHtml;
        const btnDetalle = div.querySelector('.btn-detalle');
        if (btnDetalle) {
          btnDetalle.addEventListener('click', () => mostrarDetalles(item));
        }
        resultados.appendChild(div);
      });
    } catch (error) {
      resultados.innerHTML = `<p class="text-red-500">Error: ${error.message}</p>`;
      console.error('Error en la búsqueda:', error);
    }
  }

  // Mostrar detalles en el modal
  // Mostrar detalles en el modal
  async function mostrarDetalles(item) {
    try {
      const resPagos = await fetch(`/pagos/${item.propietario_id}`);
      let pagos = [];
      if (!resPagos.ok) {
        const errorData = await resPagos.json().catch(() => ({ error: 'Error desconocido' }));
        throw new Error(errorData.error || `Error ${resPagos.status}`);
      }
      const pagosData = await resPagos.json();
      if (!Array.isArray(pagosData)) {
        console.warn('Respuesta de /pagos no es un arreglo:', pagosData);
        pagos = [];
      } else {
        pagos = pagosData;
      }

      const deuda = item.deuda ?? 0;
      const puesto = item.puesto ?? 'No asignado'; // Mostrar 'No asignado' si puesto es NULL o undefined

      let html = `
            <h2 class="text-xl font-bold">Detalles de ${item.nombre}</h2>
            <p><strong>Celular:</strong> ${item.celular}</p>
            <h3 class="mt-4">Vehículo:</h3>
            <p><strong>Placa:</strong> ${item.placa}</p>
            <p><strong>Marca:</strong> ${item.marca}</p>
            <p><strong>Modelo:</strong> ${item.modelo}</p>
            <p><strong>Año:</strong> ${item.anio}</p>
            <p><strong>Color:</strong> ${item.color}</p>
            <p><strong>Tipo:</strong> ${item.tipo}</p>
            <p><strong>Valor mensual:</strong> $${(item.valor_mensual ?? 0).toLocaleString()}</p>
            <p><strong>Puesto:</strong> ${puesto}</p>
            <p><strong>Deuda:</strong> $${deuda.toLocaleString()}</p>
            <p><strong>Estado:</strong> ${item.estado}</p>
            <h3 class="mt-4">Pagos:</h3>
            <ul>
        `;
      if (pagos.length === 0) {
        html += `<li>No hay pagos registrados</li>`;
      } else {
        pagos.forEach(p => {
          const monto = p.monto ?? 0;
          html += `<li>${p.fecha}: $${monto.toLocaleString()} - ${p.metodo || 'N/A'} - ${p.pagado ? 'Pagado' : 'Pendiente'}</li>`;
        });
      }
      html += `</ul>`;

      if (item.estado === "en mora") {
        html += `
                <button id="btn-whatsapp" class="mt-4 bg-green-500 text-white px-4 py-2 rounded" data-id="${item.propietario_id}">Enviar WhatsApp</button>
                <form id="formulario-pago" class="mt-4 hidden">
                    <div class="mb-2">
                        <label for="vehiculo-id" class="block font-bold">Vehículo</label>
                        <select id="vehiculo-id" class="w-full p-2 rounded" required>
                            <option value="" disabled selected>Seleccione un vehículo</option>
                        </select>
                    </div>
                    <div class="mb-2">
                        <label for="metodo-pago" class="block font-bold">Método de Pago</label>
                        <select id="metodo-pago" class="w-full p-2 rounded" required>
                            <option value="" disabled selected>Seleccione un método</option>
                            <option value="efectivo">Efectivo</option>
                            <option value="transferencia">Transferencia</option>
                            <option value="tarjeta">Tarjeta</option>
                            <option value="otro">Otro</option>
                        </select>
                    </div>
                    <div class="mb-2">
                        <label for="monto" class="block font-bold">Monto</label>
                        <input type="number" id="monto" class="w-full p-2 rounded" step="0.01" required>
                    </div>
                    <div class="mb-2">
                        <label for="fecha-esperado" class="block font-bold">Fecha de Pago Esperado</label>
                        <input type="date" id="fecha-esperado" class="w-full p-2 rounded" value="${new Date().toISOString().split('T')[0].slice(0, 8) + '01'}" required>
                    </div>
                    <div class="mb-2">
                        <label for="observacion" class="block font-bold">Observación (Opcional)</label>
                        <textarea id="observacion" class="w-full p-2 rounded" rows="3"></textarea>
                    </div>
                    <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded">Registrar Pago</button>
                </form>
            `;
      }

      const modalContent = document.getElementById("detalle-contenido");
      if (modalContent) {
        modalContent.innerHTML = html;
        const modal = document.getElementById("modal-detalle");
        if (modal) {
          modal.classList.remove("oculto");

          if (item.estado === "en mora") {
            cargarVehiculos(item.propietario_id);
          }

          const btnWhatsapp = document.getElementById("btn-whatsapp");
          if (btnWhatsapp) {
            btnWhatsapp.addEventListener("click", async () => {
              const id = btnWhatsapp.getAttribute("data-id");
              try {
                const res = await fetch(`/whatsapp/${id}`);
                const data = await res.json();
                if (data.enlace_whatsapp) {
                  window.open(data.enlace_whatsapp, "_blank");
                } else {
                  alert("No se pudo generar el enlace de WhatsApp.");
                }
              } catch {
                alert("Error al conectar con el servidor de WhatsApp.");
              }
            });
          }

          const btnPago = document.getElementById("btn-pago");
          if (btnPago) {
            btnPago.addEventListener("click", () => {
              const formulario = document.getElementById("formulario-pago");
              if (formulario) {
                formulario.classList.toggle("hidden");
              }
            });
          }

          const formularioPago = document.getElementById("formulario-pago");
          if (formularioPago) {
            formularioPago.addEventListener("submit", async (e) => {
              e.preventDefault();
              const propietarioId = item.propietario_id;
              const vehiculoId = document.getElementById("vehiculo-id").value;
              const metodoPago = document.getElementById("metodo-pago").value;
              const monto = document.getElementById("monto").value;
              const fechaEsperado = document.getElementById("fecha-esperado").value;
              const observacion = document.getElementById("observacion").value;

              if (!vehiculoId || !metodoPago || !monto || !fechaEsperado) {
                alert("Por favor, complete todos los campos obligatorios.");
                return;
              }

              const montoFloat = parseFloat(monto);
              if (isNaN(montoFloat) || montoFloat <= 0) {
                alert("El monto debe ser un número mayor que cero.");
                return;
              }

              const payload = {
                id_propietario: propietarioId,
                id_vehiculo: vehiculoId,
                monto: montoFloat,
                metodo: metodoPago,
                fecha_pago_esperado: fechaEsperado,
                fecha_pago_real: null,
                pagado: 1,
                observacion: observacion || null
              };
              console.log("Datos enviados a /registrar_pago:", payload);

              try {
                const res = await fetch("/registrar_pago", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                  alert("Pago registrado exitosamente");
                  formularioPago.classList.add("hidden");
                  formularioPago.reset();
                  cerrarModal();
                  buscar();
                } else {
                  alert(`Error al registrar el pago: ${data.error || "Error desconocido"}`);
                }
              } catch (error) {
                alert(`Error al registrar el pago: ${error.message}`);
              }
            });
          }
        }
      }
    } catch (error) {
      const modalContent = document.getElementById("detalle-contenido");
      if (modalContent) {
        modalContent.innerHTML = `<p>Error al cargar detalles: ${error.message}</p>`;
        document.getElementById("modal-detalle")?.classList.remove("oculto");
      }
      console.error('Error al cargar detalles:', error);
    }
  }

  async function cargarVehiculos(propietarioId) {
    try {
      const res = await fetch(`/vehiculos/${propietarioId}`);
      const vehiculos = await res.json();
      const vehiculoSelect = document.getElementById("vehiculo-id");
      if (vehiculoSelect) {
        vehiculoSelect.innerHTML = '<option value="" disabled selected>Seleccione un vehículo</option>';
        if (!Array.isArray(vehiculos) || vehiculos.length === 0) {
          vehiculoSelect.innerHTML += '<option value="" disabled>No hay vehículos registrados</option>';
        } else {
          vehiculos.forEach(v => {
            const puesto = v.puesto ?? 'No asignado';
            vehiculoSelect.innerHTML += `<option value="${v.id}">${v.placa} - ${v.marca} ${v.modelo} (Puesto: ${puesto})</option>`;
          });
        }
      }
    } catch (error) {
      console.error('Error al cargar vehículos:', error);
      alert("Error al cargar los vehículos.");
    }
  }
  // Cerrar modal
  function cerrarModal() {
    const modal = document.getElementById("modal-detalle");
    if (modal) {
      modal.classList.add("oculto"); // Corregido: oculta -> oculto
    }
  }

  // Ejecutar búsqueda al hacer clic en el botón
  btnBuscar.addEventListener("click", buscar);

  // Ejecutar búsqueda al presionar Enter
  inputBusqueda.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      buscar();
    }
  });
});