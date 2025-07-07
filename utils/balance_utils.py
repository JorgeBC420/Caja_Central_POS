def calcular_balance(registros):
    ingresos = sum(r.monto for r in registros if r.tipo == "Ingreso")
    gastos = sum(r.monto for r in registros if r.tipo == "Gasto")
    return ingresos - gastos