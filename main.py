"""Fase 4 - Programación UNAD.

Sistema de gestión de clientes, servicios y reservas sin base de datos.
Demuestra abstracción, herencia, polimorfismo, encapsulación y excepciones.
Los precios y datos de prueba son ejemplos, no valores fijados en el anexo.
"""

from abc import ABC, abstractmethod
from itertools import count
import logging
import math
from typing import overload


# El archivo de texto almacena únicamente eventos y errores, no datos del sistema.
logging.basicConfig(
    filename="eventos.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)
registrador = logging.getLogger(__name__)


# Excepciones propias para identificar errores de la aplicación.
class ErrorSistema(Exception):
    """Error general de las operaciones del sistema."""


class ErrorValidacion(ErrorSistema):
    """Un dato no cumple las condiciones requeridas."""


class ErrorServicioNoDisponible(ErrorSistema):
    """El servicio solicitado no está disponible."""


class ErrorReserva(ErrorSistema):
    """La reserva no puede realizar la operación solicitada."""


class ErrorNoEncontrado(ErrorSistema):
    """No se encontró un elemento dentro de las listas del sistema."""


# Estas funciones reúnen las validaciones repetidas en distintas clases.
def validar_texto(valor, campo):
    """Exige un texto no vacío y devuelve su versión sin espacios externos."""
    if not isinstance(valor, str) or not valor.strip():
        raise ErrorValidacion(f"{campo} debe ser un texto no vacío.")
    return valor.strip()


def validar_numero_positivo(valor, campo):
    """Acepta números positivos y finitos, pero no valores booleanos."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErrorValidacion(f"{campo} debe ser un número.")
    if not math.isfinite(valor) or valor <= 0:
        raise ErrorValidacion(f"{campo} debe ser mayor que cero y finito.")
    return float(valor)


def validar_porcentaje(valor, campo):
    """Valida porcentajes expresados de 0 a 100."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErrorValidacion(f"{campo} debe ser numérico.")
    if not math.isfinite(valor) or not 0 <= valor <= 100:
        raise ErrorValidacion(f"{campo} debe estar entre 0 y 100.")
    return float(valor)


def validar_duracion(valor):
    """Convierte una duración a entero y encadena errores de conversión."""
    try:
        # Se aceptan enteros o cadenas de dígitos, nunca decimales ni booleanos.
        if isinstance(valor, bool) or not isinstance(valor, (int, str)):
            raise ValueError("Tipo de duración no admitido")
        numero = int(valor)
        if isinstance(valor, str) and valor.strip() != str(numero):
            raise ValueError("La duración debe contener un entero")
    except ValueError as error:
        raise ErrorValidacion("La duración debe ser un número entero.") from error
    else:
        # El bloque else se ejecuta solamente si la conversión fue correcta.
        if numero <= 0:
            raise ErrorValidacion("La duración debe ser mayor que cero.")
        return numero


# Clase general abstracta solicitada por el Anexo 3.
class Entidad(ABC):
    @abstractmethod
    def mostrar_informacion(self):
        """Devuelve un texto que representa a la entidad."""


# Los datos del cliente permanecen encapsulados en atributos privados.
class Cliente(Entidad):
    def __init__(self, identificacion, nombre, correo):
        self.__identificacion = validar_texto(identificacion, "Identificación")
        self.__nombre = validar_texto(nombre, "Nombre")
        correo = validar_texto(correo, "Correo")
        # Validación básica; el anexo no determina un formato más específico.
        if correo.count("@") != 1 or "." not in correo.split("@")[-1]:
            raise ErrorValidacion("El correo electrónico no tiene un formato válido.")
        self.__correo = correo

    @property
    def identificacion(self):
        return self.__identificacion

    @property
    def nombre(self):
        return self.__nombre

    @property
    def correo(self):
        return self.__correo

    def mostrar_informacion(self):
        # No se muestra el correo para no exponer datos innecesariamente.
        return f"Cliente: {self.__nombre} (ID: {self.__identificacion})"


# Clase abstracta para los tres tipos de servicios del problema.
class Servicio(Entidad, ABC):
    def __init__(self, codigo, nombre, tarifa, disponible=True):
        self.codigo = validar_texto(codigo, "Código del servicio")
        self.nombre = validar_texto(nombre, "Nombre del servicio")
        self.tarifa = validar_numero_positivo(tarifa, "Tarifa")
        if not isinstance(disponible, bool):
            raise ErrorValidacion("Disponible debe ser verdadero o falso.")
        self.disponible = disponible

    def validar_parametros(self, duracion):
        """Comprueba la duración y la disponibilidad del servicio."""
        horas = validar_duracion(duracion)
        if not self.disponible:
            raise ErrorServicioNoDisponible(f"El servicio {self.codigo} no está disponible.")
        return horas

    def _ajustar_total(self, subtotal, descuento, impuesto):
        """Aplica descuento y después impuesto, sin costos negativos."""
        descuento = validar_porcentaje(descuento, "Descuento")
        impuesto = validar_porcentaje(impuesto, "Impuesto")
        total = subtotal * (1 - descuento / 100) * (1 + impuesto / 100)
        if not math.isfinite(total) or total < 0:
            raise ErrorValidacion("El cálculo del costo es inconsistente.")
        return round(total, 2)

    # Firmas sobrecargadas: costo sencillo o con ajustes opcionales.
    @overload
    def calcular_costo(self, duracion): ...

    @overload
    def calcular_costo(self, duracion, descuento=0, impuesto=0): ...

    @abstractmethod
    def calcular_costo(self, duracion, descuento=0, impuesto=0):
        """Calcula el precio según el tipo concreto de servicio."""

    @abstractmethod
    def describir(self):
        """Explica qué servicio ofrece la empresa."""

    def mostrar_informacion(self):
        return self.describir()


# Cada clase especializada sobrescribe los métodos requeridos.
class Sala(Servicio):
    def validar_parametros(self, duracion):
        return super().validar_parametros(duracion)

    def calcular_costo(self, duracion, descuento=0, impuesto=0):
        horas = self.validar_parametros(duracion)
        subtotal = horas * self.tarifa
        return self._ajustar_total(subtotal, descuento, impuesto)

    def describir(self):
        return f"Reserva de sala: {self.nombre}, tarifa por hora: ${self.tarifa:.2f}"


class Equipo(Servicio):
    def validar_parametros(self, duracion):
        return super().validar_parametros(duracion)

    def calcular_costo(self, duracion, descuento=0, impuesto=0):
        horas = self.validar_parametros(duracion)
        subtotal = horas * self.tarifa
        return self._ajustar_total(subtotal, descuento, impuesto)

    def describir(self):
        return f"Alquiler de equipo: {self.nombre}, tarifa por hora: ${self.tarifa:.2f}"


class Asesoria(Servicio):
    def validar_parametros(self, duracion):
        return super().validar_parametros(duracion)

    def calcular_costo(self, duracion, descuento=0, impuesto=0):
        horas = self.validar_parametros(duracion)
        subtotal = horas * self.tarifa
        return self._ajustar_total(subtotal, descuento, impuesto)

    def describir(self):
        return f"Asesoría especializada: {self.nombre}, tarifa por hora: ${self.tarifa:.2f}"


# Cada reserva relaciona un cliente, un servicio, una duración y un estado.
class Reserva(Entidad):
    _numeros = count(1)

    def __init__(self, cliente, servicio, duracion):
        if not isinstance(cliente, Cliente):
            raise ErrorValidacion("La reserva necesita un cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ErrorValidacion("La reserva necesita un servicio válido.")
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = servicio.validar_parametros(duracion)
        self.numero = next(self._numeros)
        self.estado = "pendiente"
        self.total = None

    def confirmar(self):
        if self.estado != "pendiente":
            raise ErrorReserva("Solo se puede confirmar una reserva pendiente.")
        # Validamos la disponibilidad también al confirmar.
        self.servicio.validar_parametros(self.duracion)
        self.estado = "confirmada"
        registrador.info("Reserva %s confirmada", self.numero)

    def cancelar(self):
        if self.estado == "cancelada":
            raise ErrorReserva("La reserva ya fue cancelada.")
        self.estado = "cancelada"
        registrador.info("Reserva %s cancelada", self.numero)

    def procesar(self, descuento=0, impuesto=0):
        """Calcula el costo y confirma la reserva si no hay errores."""
        if self.estado != "pendiente":
            raise ErrorReserva("Solo se puede procesar una reserva pendiente.")
        try:
            calculado = self.servicio.calcular_costo(self.duracion, descuento, impuesto)
        except (ErrorValidacion, ErrorServicioNoDisponible) as error:
            # Conserva la causa del problema sin dejar el programa detenido.
            raise ErrorReserva("No se pudo procesar la reserva.") from error
        else:
            self.total = calculado
            self.confirmar()
            return self.total

    def mostrar_informacion(self):
        return (
            f"Reserva {self.numero}: {self.cliente.nombre} - {self.servicio.nombre} "
            f"({self.duracion} h) - {self.estado}"
        )


# El sistema almacena sus datos únicamente en listas de objetos.
class Sistema:
    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []

    def registrar_cliente(self, identificacion, nombre, correo):
        cliente = Cliente(identificacion, nombre, correo)
        if any(c.identificacion == cliente.identificacion for c in self.clientes):
            raise ErrorValidacion("La identificación del cliente ya está registrada.")
        self.clientes.append(cliente)
        registrador.info("Cliente registrado: %s", cliente.identificacion)
        return cliente

    def registrar_servicio(self, servicio):
        if not isinstance(servicio, Servicio):
            raise ErrorValidacion("El objeto debe ser un servicio especializado.")
        if any(s.codigo == servicio.codigo for s in self.servicios):
            raise ErrorValidacion("El código del servicio ya está registrado.")
        self.servicios.append(servicio)
        registrador.info("Servicio registrado: %s", servicio.codigo)
        return servicio

    def crear_reserva(self, cliente, servicio, duracion):
        if cliente not in self.clientes:
            raise ErrorNoEncontrado("El cliente no está registrado en el sistema.")
        if servicio not in self.servicios:
            raise ErrorNoEncontrado("El servicio no está registrado en el sistema.")
        reserva = Reserva(cliente, servicio, duracion)
        self.reservas.append(reserva)
        registrador.info("Reserva creada: %s", reserva.numero)
        return reserva


# El simulador registra los resultados y continúa después de cada error.
def ejecutar_operacion(numero, descripcion, accion):
    print(f"\n{numero:02d}. {descripcion}")
    try:
        resultado = accion()
    except ErrorSistema as error:
        print(f"   ERROR CONTROLADO: {error}")
        registrador.error("Operación %s (%s): %s", numero, descripcion, error, exc_info=True)
    except Exception:
        # Captura final para que una falla no prevista quede registrada.
        print("   ERROR INESPERADO: consultar eventos.log")
        registrador.exception("Operación %s (%s): error inesperado", numero, descripcion)
    else:
        print(f"   CORRECTO: {resultado}")
        registrador.info("Operación %s completada: %s", numero, descripcion)
    finally:
        # Este bloque siempre se ejecuta, aun cuando ocurre una excepción.
        print("   Operación finalizada.")


def simular():
    """Ejecuta más de 10 operaciones válidas e inválidas del Anexo 3."""
    sistema = Sistema()
    elementos = {}  # Referencias temporales para relacionar las operaciones.

    def guardar(clave, funcion):
        elementos[clave] = funcion()
        return elementos[clave].mostrar_informacion()

    ejecutar_operacion(1, "Registrar cliente válido", lambda: guardar(
        "ana", lambda: sistema.registrar_cliente("1001", "Ana Pérez", "ana@correo.com")))
    ejecutar_operacion(2, "Registrar cliente con correo inválido", lambda:
        sistema.registrar_cliente("1002", "Cliente Inválido", "correo_incorrecto"))
    ejecutar_operacion(3, "Registrar segundo cliente válido", lambda: guardar(
        "luis", lambda: sistema.registrar_cliente("1003", "Luis Gómez", "luis@correo.com")))
    ejecutar_operacion(4, "Registrar sala", lambda: guardar(
        "sala", lambda: sistema.registrar_servicio(Sala("S1", "Sala de reuniones", 30000))))
    ejecutar_operacion(5, "Registrar equipo", lambda: guardar(
        "equipo", lambda: sistema.registrar_servicio(Equipo("E1", "Proyector", 20000))))
    ejecutar_operacion(6, "Registrar asesoría", lambda: guardar(
        "asesoria", lambda: sistema.registrar_servicio(Asesoria("A1", "Asesoría técnica", 50000))))
    ejecutar_operacion(7, "Crear servicio con tarifa incorrecta", lambda:
        sistema.registrar_servicio(Sala("S2", "Sala inválida", -1000)))
    ejecutar_operacion(8, "Crear reserva de sala", lambda: guardar(
        "reserva_sala", lambda: sistema.crear_reserva(elementos["ana"], elementos["sala"], 2)))
    ejecutar_operacion(9, "Procesar reserva de sala", lambda:
        f"Total: ${elementos['reserva_sala'].procesar():.2f}")
    ejecutar_operacion(10, "Crear reserva de equipo", lambda: guardar(
        "reserva_equipo", lambda: sistema.crear_reserva(elementos["luis"], elementos["equipo"], 3)))
    ejecutar_operacion(11, "Procesar equipo con descuento e impuesto", lambda:
        f"Total: ${elementos['reserva_equipo'].procesar(descuento=10, impuesto=19):.2f}")
    ejecutar_operacion(12, "Crear reserva de asesoría", lambda: guardar(
        "reserva_asesoria", lambda: sistema.crear_reserva(elementos["ana"], elementos["asesoria"], 1)))
    ejecutar_operacion(13, "Confirmar asesoría", lambda:
        (elementos["reserva_asesoria"].confirmar() or "Reserva confirmada"))
    ejecutar_operacion(14, "Intentar reserva con duración cero", lambda:
        sistema.crear_reserva(elementos["ana"], elementos["sala"], 0))
    ejecutar_operacion(15, "Intentar reserva sin disponibilidad", lambda:
        (setattr(elementos["equipo"], "disponible", False) or
         sistema.crear_reserva(elementos["ana"], elementos["equipo"], 2)))
    ejecutar_operacion(16, "Cancelar reserva de asesoría", lambda:
        (elementos["reserva_asesoria"].cancelar() or "Reserva cancelada"))
    ejecutar_operacion(17, "Intentar confirmar reserva cancelada", lambda:
        elementos["reserva_asesoria"].confirmar())
    ejecutar_operacion(18, "Registrar cliente duplicado", lambda:
        sistema.registrar_cliente("1001", "Otra Ana", "otra@correo.com"))
    ejecutar_operacion(19, "Intentar reserva con duración no numérica", lambda:
        sistema.crear_reserva(elementos["ana"], elementos["sala"], "dos"))

    print("\nRESUMEN DE LOS OBJETOS EN MEMORIA")
    print(f"Clientes: {len(sistema.clientes)}")
    print(f"Servicios: {len(sistema.servicios)}")
    print(f"Reservas: {len(sistema.reservas)}")
    print("Los eventos y errores se registraron en eventos.log")


# Este punto de entrada evita ejecutar la simulación al importar el módulo.
if __name__ == "__main__":
    simular()
