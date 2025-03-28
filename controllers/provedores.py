from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models.models import Proveedor, db
from forms import ProveedoresForm

from controllers.auth import rol_required


provedores_bp = Blueprint('provedores', __name__)

@provedores_bp.route('/proveedores', methods=['GET', 'POST'])
@rol_required(2)
@login_required
def index():
    form = ProveedoresForm()
    proveedores = Proveedor.query.all()
    
    if request.method == 'POST' and form.validate_on_submit():
        nuevo_proveedor = Proveedor(
            nombre=form.nombre.data,
            empresa=form.empresa.data,
            telefono=form.telefono.data
        )
        db.session.add(nuevo_proveedor)
        db.session.commit()
        flash('Proveedor agregado correctamente', 'success')
        return redirect(url_for('provedores.index'))
    
    return render_template('proveedores.html', form=form, proveedores=proveedores)

@provedores_bp.route('/eliminar_proveedor/<int:id>')
@rol_required(2)
@login_required
def eliminar(id):
    proveedor = Proveedor.query.get_or_404(id)
    db.session.delete(proveedor)
    db.session.commit()
    flash('Proveedor eliminado correctamente', 'success')
    return redirect(url_for('provedores.index'))

@provedores_bp.route('/editar_proveedor/<int:id>', methods=['GET', 'POST'])
@rol_required(2)
@login_required
def editar(id):
    proveedor = Proveedor.query.get_or_404(id)
    form = ProveedoresForm(obj=proveedor)
    
    if request.method == 'POST' and form.validate_on_submit():
        proveedor.nombre = form.nombre.data
        proveedor.empresa = form.empresa.data
        proveedor.telefono = form.telefono.data
        db.session.commit()
        flash('Proveedor actualizado correctamente', 'success')
        return redirect(url_for('provedores.editar', id=id))
    
    return render_template('editar_proveedor.html', form=form, proveedor=proveedor)