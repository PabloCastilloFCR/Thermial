import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import calendar

def find_header_row(file_path, header_keyword='Fecha/Hora'):
    """
    Encuentra la fila en la que se encuentra el encabezado de los datos.
    Args:
        file_path (str): Ruta al archivo CSV.
        header_keyword (str): Una cadena de texto única en la fila del encabezado.
    Returns:
        int: El número de la fila del encabezado (basado en 0) o None si no se encuentra.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if header_keyword in line:
                return i
    return None

def analizar_tmy_ghi(file_path, modo="explorar"):
    """
    Carga un archivo TMY, permite al usuario seleccionar un mes y grafica el GHI
    para todos los días de ese mes.
    Args:
        file_path (str): La ruta al archivo CSV.
    """
    try:
        # 1. Encontrar la fila del encabezado para saltar los metadatos
        header_row = find_header_row(file_path)
        if header_row is None:
            print("No se pudo encontrar la fila del encabezado con 'Fecha/Hora'.")
            return

        # 2. Cargar el archivo CSV con pandas, saltando las filas de metadatos
        df = pd.read_csv(file_path, skiprows=header_row, encoding='utf-8')

        # 3. Procesar las fechas y establecerlas como índice
        df['Fecha/Hora'] = pd.to_datetime(df['Fecha/Hora'])
        df.set_index('Fecha/Hora', inplace=True)

        # Extraer componentes de la fecha para facilitar el filtrado y ploteo
        df['month'] = df.index.month
        df['day'] = df.index.day
        df['hour'] = df.index.hour

        # 4. Mostrar los meses disponibles y solicitar selección al usuario
        available_months = sorted(df['month'].unique())
        print("Meses presentes en el archivo de datos:")
        for month_num in available_months:
            print(f"- {month_num}: {calendar.month_name[month_num]}")

        selected_month = 0
        while selected_month not in available_months:
            try:
                selected_month = int(input(f"\nSeleccione el número del mes que desea graficar: "))
                if selected_month not in available_months:
                    print("Mes no válido. Por favor, intente de nuevo.")
            except ValueError:
                print("Por favor, ingrese un número válido.")

                # 5. Lógica para los dos modos
        if modo == "explorar":
            visualizar_mes(df, selected_month)
        elif modo == "exportar":
            visualizar_dia_normalizado(df, selected_month)

    except FileNotFoundError:
         print(f"Error: El archivo no se encontró en la ruta '{file_path}'")
    except KeyError as e:
        print(f"Error: La columna esperada '{e}' no se encontró en el archivo CSV.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

def visualizar_mes(df, selected_month):        
        # 5. Filtrar el DataFrame para el mes seleccionado
        month_data = df[df['month'] == selected_month]

        # 6. Preparar la cuadrícula de subgráficos
        days_in_month = sorted(month_data['day'].unique())
        num_days = len(days_in_month)
        rows = 5
        cols = 7

        fig, axes = plt.subplots(rows, cols, sharex=True, sharey=True)
        fig.suptitle(f'Irradiancia Global Horizontal (GHI) en {calendar.month_name[selected_month]} - Gráficos Diarios', fontsize=20)
        axes = axes.flatten()  # Convertir el array de axes en una lista plana para facilitar la iteración

        # 7. Graficar GHI vs. Hora para cada día del mes en un subgráfico individual
        for i, day in enumerate(days_in_month):  
            day_data = month_data[month_data['day'] == day]
            ax = axes[i]
            ax.plot(day_data['hour'], day_data['ghi'], label=f'Día {day}', color='steelblue')
            ax.set_title(f'Día {day}', fontsize=10)
            ax.set_xticks(np.arange(0, 24, 6))  # Mostrar cada 6 horas en el eje X
            ax.set_xlim(0, 23)
            ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

            # Solo añadir etiquetas en los gráficos de los bordes para evitar repetición
            if i >= (rows - 1) * cols:  # Última fila
                ax.set_xlabel('Hora', fontsize=10)
            if i % cols == 0:  # Primera columna
                ax.set_ylabel('GHI (W/m²)', fontsize=10)

        # 8. Ocultar los subgráficos vacíos si el mes tiene menos de 35 días
        for j in range(num_days, len(axes)):
            axes[j].axis('off')

        # Maximizar la ventana del gráfico
        fig.set_size_inches(17, 9)  # Ajustar el tamaño de la figura antes de mostrarla
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Ajustar el layout para que no se superponga con el título principal
        plt.show()

def visualizar_dia_normalizado(df, selected_month):
    """
    Permite al usuario seleccionar un día de un mes específico, grafica el GHI normalizado
    para ese día y luego pide una duración de experimento para mostrar un segundo
    gráfico con los datos de GHI rescalados a esa duración.
    Args:
        df (pd.DataFrame): DataFrame con los datos TMY.
        selected_month (int): El mes seleccionado por el usuario.
    """
    # 5. Seleccionar un día específico
    selected_day = 0
    available_days = sorted(df[df['month'] == selected_month]['day'].unique())
    while selected_day not in available_days:
        try:
            selected_day = int(input(f"Seleccione un día del mes ({min(available_days)}-{max(available_days)}): "))
            if selected_day not in available_days:
                print("Día no válido. Por favor, intente de nuevo.")
        except ValueError:
            print("Por favor, ingrese un número válido.")

    # 6. Filtrar datos para el día seleccionado
    day_data = df[(df['month'] == selected_month) & (df['day'] == selected_day)].copy()

    # 7. Calcular el GHI máximo anual
    max_ghi_anual = df['ghi'].max()

    # 8. Normalizar los datos del día seleccionado
    if max_ghi_anual > 0:
        day_data['ghi_normalizado'] = (day_data['ghi'] / max_ghi_anual) * 100
    else:
        day_data['ghi_normalizado'] = 0  # Evitar división por cero

    # 9. Graficar los datos normalizados
    plt.figure(figsize=(12, 6))
    plt.plot(day_data['hour'], day_data['ghi_normalizado'], marker='o', linestyle='-')
    plt.title(f'GHI Normalizado para el Día {selected_day} de {calendar.month_name[selected_month]}', fontsize=16)
    plt.xlabel('Hora del día', fontsize=12)
    plt.ylabel('GHI Normalizado (% del máximo anual)', fontsize=12)
    plt.xticks(range(0, 24))
    plt.grid(True)
    plt.show()

    # --- Funcionalidad añadida para seleccionar rango horario ---

    # 10. Preguntar por el rango horario
    while True:
        try:
            rango_horario_str = input("Ingrese el rango horario a seleccionar (formato: inicio-fin, ej: 6-19): ")
            inicio_str, fin_str = rango_horario_str.split('-')
            hora_inicio = int(inicio_str)
            hora_fin = int(fin_str)
            if 0 <= hora_inicio < hora_fin <= 24:
                break
            else:
                print("Rango horario no válido. Asegúrese de que el inicio esté entre 0 y 23, el fin entre 1 y 24, y el inicio sea menor que el fin.")
        except ValueError:
            print("Formato no válido. Use el formato inicio-fin (ej: 6-19).")

    # 11. Filtrar los datos por el rango horario y reajustar las horas
    day_data = day_data[(day_data['hour'] >= hora_inicio) & (day_data['hour'] < hora_fin)].copy()
    day_data['hour_adj'] = day_data['hour'] - hora_inicio

    # Si el rango incluye la medianoche (ej., 18-6), ajustamos para que las horas sean consecutivas
    if hora_inicio > hora_fin:
        day_data.loc[day_data['hour'] < hora_inicio, 'hour_adj'] += (24 - hora_inicio)

    # --- Funcionalidad añadida para reescalar el tiempo ---

    # 12. Preguntar por la duración del experimento
    duracion_minutos = 0
    while True:
        try:
            duracion_str = input("Cuantos minutos durara la duración del experimento? (1-600): ")
            duracion_minutos = int(duracion_str)
            if 1 <= duracion_minutos <= 600:
                break
            else:
                print("Por favor, ingrese un número entre 1 y 600.")
        except ValueError:
            print("Entrada no válida. Por favor, ingrese un número.")

    # 13. Rescalar el eje de tiempo usando 'hour_adj'
    # Calcula la duración total del rango horario seleccionado
    rango_total_horas = (hora_fin - hora_inicio) if hora_fin > hora_inicio else (24 - hora_inicio + hora_fin)
    day_data['tiempo_experimento'] = day_data['hour_adj'] / (rango_total_horas -1) * duracion_minutos

    # 14. Graficar los datos normalizados con el tiempo reescalado
    plt.figure(figsize=(12, 6))
    plt.plot(day_data['tiempo_experimento'], day_data['ghi_normalizado'], marker='o', linestyle='-', color='r')
    plt.title(f'Perfil GHI Rescalado a {duracion_minutos} Minutos (Rango {hora_inicio}-{hora_fin}h)', fontsize=16)
    plt.xlabel('Tiempo del Experimento (minutos)', fontsize=12)
    plt.ylabel('GHI Normalizado (% del máximo anual)', fontsize=12)
    plt.xlim(0, duracion_minutos)
    plt.grid(True)
    plt.show()


def main():
    file_path = r'c:\Users\Pablo Castillo\OneDrive - fraunhofer.cl\Documentos\GitHub\Thermial\controlador (Pi 4)\real_data_experiment\tmy_profile\DHTMY_E_5IB2JJ.csv'
    modo = input("Seleccione el modo ('explorar' o 'exportar'): ").lower()
    if modo not in ['explorar', 'exportar']:
        print("Modo no válido. Se ejecutará el modo 'explorar' por defecto.")
        modo = 'explorar'
    analizar_tmy_ghi(file_path, modo)
# --- Ejecución del Script ---
if __name__ == "__main__":
    main()