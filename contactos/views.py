from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from .forms import ContactoForm
from .models import Contacto


# Vista para listar contactos con búsqueda y paginación
def contacto_list(request):
    query = request.GET.get('q', '').strip()
    contactos_qs = Contacto.objects.all().order_by('nombre')

    if query:
        contactos_qs = contactos_qs.filter(
            Q(nombre__icontains=query) | Q(correo__icontains=query)
        )

    # Paginación: 12 contactos por página (conforme a indicadores de evaluación)
    paginator = Paginator(contactos_qs, 12)
    page_number = request.GET.get('page')
    contactos = paginator.get_page(page_number)

    return render(request, 'contactos/contacto_list.html', {
        'contactos': contactos,
        'query': query,
    })


# Vista para ver los detalles de un contacto por su id
def contacto_detail(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk)
    return render(request, 'contactos/contacto_detail.html', {'contacto': contacto})


# Vista para crear un nuevo contacto
def contacto_create(request):
    form = ContactoForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        contacto = form.save()
        messages.success(request, f'Contacto "{contacto.nombre}" creado exitosamente.')
        return redirect('contacto_list')

    return render(request, 'contactos/contacto_form.html', {'form': form, 'modo': 'Agregar'})


# Vista para editar los datos de un contacto existente
def contacto_update(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk)
    form = ContactoForm(request.POST or None, instance=contacto)

    if request.method == 'POST' and form.is_valid():
        contacto = form.save()
        messages.success(request, f'Contacto "{contacto.nombre}" actualizado exitosamente.')
        return redirect('contacto_detail', pk=contacto.pk)

    return render(request, 'contactos/contacto_form.html', {
        'form': form,
        'modo': 'Editar',
        'contacto': contacto,
    })


# Vista para borrar un contacto con confirmación
def contacto_delete(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk)

    if request.method == 'POST':
        nombre = contacto.nombre
        contacto.delete()
        messages.success(request, f'Contacto "{nombre}" eliminado exitosamente.')
        return redirect('contacto_list')

    return render(request, 'contactos/contacto_confirm_delete.html', {'contacto': contacto})


# Vista para borrar múltiples contactos con confirmación previa
def contacto_bulk_delete(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_ids')

        if not selected_ids:
            return redirect('contacto_list')

        if request.POST.get('confirmar') == '1':
            total = len(selected_ids)
            Contacto.objects.filter(pk__in=selected_ids).delete()
            messages.success(request, f'Se han eliminado {total} contacto(s) exitosamente.')
            return redirect('contacto_list')

        contactos = Contacto.objects.filter(pk__in=selected_ids)
        if not contactos.exists():
            return redirect('contacto_list')

        return render(request, 'contactos/contacto_bulk_confirm_delete.html', {
            'contactos': contactos,
            'selected_ids': selected_ids,
        })

    return redirect('contacto_list')


# ==============================================================================
# INTEGRACIÓN MÓVIL HÍBRIDA (vCard .vcf de ida y vuelta)
# ==============================================================================

def _build_vcard_entry(c):
    """Genera la estructura estándar vCard 3.0 para un contacto."""
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{c.nombre}",
    ]
    parts = c.nombre.strip().split()
    if len(parts) > 1:
        lines.append(f"N:{parts[-1]};{' '.join(parts[:-1])};;;")
    else:
        lines.append(f"N:{c.nombre};;;;")

    if c.telefono:
        lines.append(f"TEL;TYPE=CELL:{c.telefono}")
    if c.correo:
        lines.append(f"EMAIL;TYPE=INTERNET:{c.correo}")
    if c.direccion:
        lines.append(f"ADR;TYPE=HOME:;;{c.direccion};;;;")
    lines.append("END:VCARD")
    return "\r\n".join(lines) + "\r\n"


def contacto_vcard_download(request, pk):
    """Descarga la ficha vCard individual para que el celular la agregue a su libreta."""
    contacto = get_object_or_404(Contacto, pk=pk)
    vcard_data = _build_vcard_entry(contacto)
    filename = f"{slugify(contacto.nombre) or 'contacto'}.vcf"

    response = HttpResponse(vcard_data, content_type='text/vcard; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def contactos_vcard_export_all(request):
    """Descarga todos los contactos de la base de datos en un solo archivo .vcf para el celular."""
    contactos = Contacto.objects.all().order_by('nombre')
    if not contactos.exists():
        messages.warning(request, "No hay contactos guardados para exportar.")
        return redirect('contacto_list')

    all_vcards = "".join(_build_vcard_entry(c) for c in contactos)
    response = HttpResponse(all_vcards, content_type='text/vcard; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="contactos_agenda.vcf"'
    return response



def contactos_vcard_export_selected(request):
    """Descarga solo los contactos seleccionados en un archivo .vcf para el celular."""
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_ids')
        if not selected_ids:
            messages.warning(request, "No seleccionaste ningún contacto para exportar.")
            return redirect('contacto_list')

        contactos = Contacto.objects.filter(pk__in=selected_ids).order_by('nombre')
        all_vcards = "".join(_build_vcard_entry(c) for c in contactos)
        filename = f"contactos_seleccionados_{len(selected_ids)}.vcf"

        response = HttpResponse(all_vcards, content_type='text/vcard; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    return redirect('contacto_list')


def contacto_vcard_import(request):
    """Importa contactos desde un archivo .vcf exportado por un teléfono (Android o iOS)."""
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_vcf')
        if not archivo:
            messages.error(request, "Por favor selecciona un archivo .vcf para importar.")
            return render(request, 'contactos/contacto_import_vcf.html')

        if not archivo.name.lower().endswith('.vcf'):
            messages.error(request, "El archivo debe tener extensión .vcf (formato vCard).")
            return render(request, 'contactos/contacto_import_vcf.html')

        try:
            raw_content = archivo.read()
            try:
                content = raw_content.decode('utf-8')
            except UnicodeDecodeError:
                content = raw_content.decode('iso-8859-1', errors='ignore')

            # Desplegar líneas continuadas (folding vCard)
            unfolded = []
            for line in content.splitlines():
                if line.startswith((' ', '\t')) and unfolded:
                    unfolded[-1] += line[1:]
                else:
                    unfolded.append(line)

            creados = 0
            duplicados = 0
            current = None

            for line in unfolded:
                line_str = line.strip()
                if not line_str:
                    continue

                if line_str.upper().startswith('BEGIN:VCARD'):
                    current = {'nombre': '', 'telefono': '', 'correo': '', 'direccion': ''}
                elif line_str.upper().startswith('END:VCARD') and current:
                    nombre = current['nombre'].strip()
                    telefono = current['telefono'].strip()
                    correo = current['correo'].strip()
                    direccion = current['direccion'].strip()

                    if nombre:
                        # Si no viene correo, generamos uno referencial
                        if not correo:
                            correo = f"{slugify(nombre)}@sin-correo.cl"

                        # Verificamos si ya existe por nombre o correo
                        existe = Contacto.objects.filter(
                            Q(nombre__iexact=nombre) | (Q(correo__iexact=correo) if correo else Q())
                        ).exists()

                        if not existe:
                            Contacto.objects.create(
                                nombre=nombre,
                                telefono=telefono or "+56 9 0000 0000",
                                correo=correo,
                                direccion=direccion,
                            )
                            creados += 1
                        else:
                            duplicados += 1
                    current = None
                elif current is not None:
                    upper = line_str.upper()
                    if upper.startswith('FN:') or upper.startswith('FN;'):
                        current['nombre'] = line_str.split(':', 1)[1].strip()
                    elif (upper.startswith('N:') or upper.startswith('N;')) and not current['nombre']:
                        parts = line_str.split(':', 1)[1].split(';')
                        clean = [p.strip() for p in parts if p.strip()]
                        clean.reverse()
                        current['nombre'] = ' '.join(clean)
                    elif upper.startswith('TEL') and ':' in line_str:
                        if not current['telefono']:
                            current['telefono'] = line_str.split(':', 1)[1].strip()
                    elif upper.startswith('EMAIL') and ':' in line_str:
                        if not current['correo']:
                            current['correo'] = line_str.split(':', 1)[1].strip()
                    elif upper.startswith('ADR') and ':' in line_str:
                        if not current['direccion']:
                            adr = line_str.split(':', 1)[1].split(';')
                            current['direccion'] = ', '.join([p.strip() for p in adr if p.strip()])

            if creados > 0:
                msg = f"¡Éxito! Se han importado {creados} contacto(s) desde tu teléfono a la base de datos."
                if duplicados > 0:
                    msg += f" ({duplicados} omitidos por ya existir)."
                messages.success(request, msg)
            elif duplicados > 0:
                messages.info(request, f"Todos los contactos del archivo ({duplicados}) ya existen en tu agenda.")
            else:
                messages.warning(request, "No se encontraron contactos válidos en el archivo vCard subido.")

            return redirect('contacto_list')

        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar el archivo vCard: {str(e)}")
            return render(request, 'contactos/contacto_import_vcf.html')

    return render(request, 'contactos/contacto_import_vcf.html')
