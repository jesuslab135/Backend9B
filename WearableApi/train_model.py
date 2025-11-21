import os
import sys
import django
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WearableApi.settings')
django.setup()

from api.models import Lectura, Ventana, Analisis, Consumidor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, classification_report

def extract_features_from_lecturas():
    print("📊 Extrayendo datos de la base de datos...")
    
    lecturas = Lectura.objects.select_related('ventana').all()
    
    if lecturas.count() == 0:
        print("❌ No hay lecturas en la base de datos!")
        print("💡 Sugerencia: Inserta datos de prueba primero")
        return None
    
    print(f"✅ Encontradas {lecturas.count()} lecturas")
    
    data = []
    for lectura in lecturas:
        data.append({
            'ventana_id': lectura.ventana_id,
            'heart_rate': lectura.heart_rate or 0,
            'accel_x': lectura.accel_x or 0,
            'accel_y': lectura.accel_y or 0,
            'accel_z': lectura.accel_z or 0,
            'gyro_x': lectura.gyro_x or 0,
            'gyro_y': lectura.gyro_y or 0,
            'gyro_z': lectura.gyro_z or 0,
        })
    
    df = pd.DataFrame(data)
    return df

def engineer_features(df):
    print("🔧 Creando features adicionales...")
    
    features_per_window = []
    
    for ventana_id in df['ventana_id'].unique():
        window_data = df[df['ventana_id'] == ventana_id]
        
        features = {
            'ventana_id': ventana_id,
            
            'hr_mean': window_data['heart_rate'].mean(),
            'hr_std': window_data['heart_rate'].std(),
            'hr_min': window_data['heart_rate'].min(),
            'hr_max': window_data['heart_rate'].max(),
            'hr_range': window_data['heart_rate'].max() - window_data['heart_rate'].min(),
            
            'accel_magnitude_mean': np.sqrt(
                window_data['accel_x']**2 + 
                window_data['accel_y']**2 + 
                window_data['accel_z']**2
            ).mean(),
            'accel_magnitude_std': np.sqrt(
                window_data['accel_x']**2 + 
                window_data['accel_y']**2 + 
                window_data['accel_z']**2
            ).std(),
            
            'gyro_magnitude_mean': np.sqrt(
                window_data['gyro_x']**2 + 
                window_data['gyro_y']**2 + 
                window_data['gyro_z']**2
            ).mean(),
            'gyro_magnitude_std': np.sqrt(
                window_data['gyro_x']**2 + 
                window_data['gyro_y']**2 + 
                window_data['gyro_z']**2
            ).std(),
            
            'accel_energy': (window_data['accel_x']**2 + 
                           window_data['accel_y']**2 + 
                           window_data['accel_z']**2).sum(),
            'gyro_energy': (window_data['gyro_x']**2 + 
                          window_data['gyro_y']**2 + 
                          window_data['gyro_z']**2).sum(),
        }
        
        features_per_window.append(features)
    
    features_df = pd.DataFrame(features_per_window)
    
    features_df = features_df.fillna(0)
    
    print(f"✅ Creadas {len(features_df.columns)-1} features para {len(features_df)} ventanas")
    
    return features_df

def get_labels():
    print("🏷️  Obteniendo labels...")
    
    analisis = Analisis.objects.all()
    
    if analisis.count() > 0:
        labels_data = []
        for a in analisis:
            labels_data.append({
                'ventana_id': a.ventana_id,
                'urge_label': a.urge_label
            })
        labels_df = pd.DataFrame(labels_data)
        print(f"✅ Encontrados {len(labels_df)} labels reales")
        return labels_df
    
    print("⚠️  No hay análisis previos. Generando labels sintéticos...")
    print("💡 En producción, debes etiquetar los datos realmente")
    
    ventanas = Ventana.objects.all()
    if ventanas.count() == 0:
        print("❌ No hay ventanas en la base de datos")
        return None
    
    labels_data = []
    for ventana in ventanas:
        lecturas = Lectura.objects.filter(ventana=ventana)
        if lecturas.exists():
            hr_mean = lecturas.aggregate(hr=models.Avg('heart_rate'))['hr'] or 70
            urge_label = 1 if hr_mean > 90 else 0
        else:
            urge_label = 0
        
        labels_data.append({
            'ventana_id': ventana.id,
            'urge_label': urge_label
        })
    
    labels_df = pd.DataFrame(labels_data)
    print(f"✅ Generados {len(labels_df)} labels sintéticos")
    print("⚠️  Recuerda: estos son datos de prueba, no reales")
    
    return labels_df

def train_model():
    print("\n" + "="*60)
    print("🚀 ENTRENAMIENTO DEL MODELO DE PREDICCIÓN")
    print("="*60 + "\n")
    
    lecturas_df = extract_features_from_lecturas()
    if lecturas_df is None:
        return False
    
    features_df = engineer_features(lecturas_df)
    
    labels_df = get_labels()
    if labels_df is None:
        return False
    
    print("\n🔗 Combinando features y labels...")
    data = features_df.merge(labels_df, on='ventana_id', how='inner')
    
    if len(data) == 0:
        print("❌ No hay datos para entrenar después del merge")
        return False
    
    print(f"✅ Dataset final: {len(data)} muestras")
    
    X = data.drop(['ventana_id', 'urge_label'], axis=1)
    y = data['urge_label']
    
    print(f"\n📊 Distribución de clases:")
    print(f"   - Sin deseo (0): {(y == 0).sum()} muestras ({(y == 0).mean()*100:.1f}%)")
    print(f"   - Con deseo (1): {(y == 1).sum()} muestras ({(y == 1).mean()*100:.1f}%)")
    
    print("\n✂️  Dividiendo datos en train/test (80/20)...")
    
    min_class_count = y.value_counts().min()
    use_stratify = min_class_count >= 2 and len(y.unique()) > 1
    
    if not use_stratify:
        print(f"⚠️  Estratificación desactivada (muy pocos datos en alguna clase)")
        print(f"   Mínimo por clase: {min_class_count} muestras")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=0.2, 
        random_state=42,
        stratify=y if use_stratify else None
    )
    
    print(f"   - Train: {len(X_train)} muestras")
    print(f"   - Test: {len(X_test)} muestras")
    
    print("\n🔄 Normalizando features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("\n🎓 Entrenando Logistic Regression...")
    model = LogisticRegression(
        max_iter=1000,
        random_state=42,
        class_weight='balanced',
        C=0.1,
        penalty='l2',
        solver='lbfgs'
    )
    model.fit(X_train_scaled, y_train)
    print("✅ Modelo entrenado!")
    
    print("\n📈 Evaluando modelo...")
    
    y_train_pred = model.predict(X_train_scaled)
    train_accuracy = accuracy_score(y_train, y_train_pred)
    
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    print(f"\n✅ MÉTRICAS DEL MODELO:")
    print(f"   📚 Train Accuracy: {train_accuracy:.3f}")
    print(f"   📊 Test Metrics:")
    print(f"      - Accuracy:  {accuracy:.3f}")
    print(f"      - Precision: {precision:.3f}")
    print(f"      - Recall:    {recall:.3f}")
    print(f"      - F1-Score:  {f1:.3f}")
    
    if train_accuracy - accuracy > 0.15:
        print(f"\n⚠️  WARNING: Posible overfitting detectado!")
        print(f"   Train accuracy ({train_accuracy:.3f}) >> Test accuracy ({accuracy:.3f})")
        print(f"   Considera: más datos, más regularización, o features más simples")
    
    if len(y_test.unique()) > 1:
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        print(f"      - ROC-AUC:   {roc_auc:.3f}")
    
    print("\n📊 Reporte de clasificación:")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    os.makedirs('models', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_path = f'models/smoking_craving_model_{timestamp}.pkl'
    
    print(f"\n💾 Guardando modelo en: {model_path}")
    
    model_package = {
        'model': model,
        'scaler': scaler,
        'feature_names': X.columns.tolist(),
        'training_date': datetime.now().isoformat(),
        'metrics': {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    }
    
    joblib.dump(model_package, model_path)
    print("✅ Modelo guardado!")
    
    latest_model_path = 'models/smoking_craving_model.pkl'
    if os.path.exists(latest_model_path):
        os.remove(latest_model_path)
    
    import shutil
    shutil.copy(model_path, latest_model_path)
    print(f"✅ Symlink creado: {latest_model_path}")
    
    print("\n" + "="*60)
    print("🎉 ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
    print("="*60)
    print(f"\n📁 Modelo guardado en: {latest_model_path}")
    print(f"🔧 Ahora puedes usar Celery para hacer predicciones!")
    
    return True

def generate_synthetic_window(consumidor, pattern_type):
    """
    Helper to generate a window with specific patterns:
    - 'rest': Low HR, Low Motion (Label 0)
    - 'exercise': High HR, High Motion (Label 0)
    - 'craving': Elevated HR, Low Motion (Label 1)
    """
    from django.utils import timezone
    
    window_start = timezone.now() - timezone.timedelta(days=np.random.randint(0, 30))
    ventana = Ventana.objects.create(
        consumidor=consumidor,
        window_start=window_start,
        window_end=window_start + timezone.timedelta(minutes=5)
    )
    
    # Define base parameters based on pattern
    if pattern_type == 'craving':
        # CRAVING: Elevated HR but user is sitting still (anxiety/stress)
        hr_base = np.random.uniform(85, 100)
        motion_intensity = 0.1  # Very low motion
        urge_label = 1
    elif pattern_type == 'exercise':
        # EXERCISE: High HR and High Motion
        hr_base = np.random.uniform(110, 140)
        motion_intensity = 2.5  # High motion
        urge_label = 0
    else: # 'rest'
        # REST: Low HR and Low Motion
        hr_base = np.random.uniform(60, 75)
        motion_intensity = 0.2  # Low motion
        urge_label = 0
        
    for _ in range(30):
        # Add some random fluctuation
        hr = np.random.normal(hr_base, 5)
        
        # Motion components
        accel = np.random.normal(motion_intensity, motion_intensity * 0.5)
        gyro = np.random.normal(motion_intensity * 0.5, motion_intensity * 0.2)
        
        Lectura.objects.create(
            ventana=ventana,
            heart_rate=max(50, min(180, hr)),
            accel_x=accel * np.random.randn(),
            accel_y=accel * np.random.randn(),
            accel_z=accel * np.random.randn(),
            gyro_x=gyro * np.random.randn(),
            gyro_y=gyro * np.random.randn(),
            gyro_z=gyro * np.random.randn()
        )
        
    # Create analysis label
    Analisis.objects.create(
        ventana=ventana,
        probabilidad_modelo=0.9 if urge_label == 1 else 0.1,
        urge_label=urge_label,
        modelo_usado='manual_training_data'
    )
    return ventana

def insert_sample_data():
    print("\n🔧 ¿Quieres insertar datos de muestra MEJORADOS? (y/n): ", end='')
    response = input().strip().lower()
    
    if response != 'y':
        return
    
    print("\n📝 Insertando datos de entrenamiento inteligentes...")
    
    try:
        from api.models import Usuario
        # Try to find a consumer, or use test user
        usuario = Usuario.objects.filter(consumidor__isnull=False).first()
        if not usuario:
            print("❌ No hay usuarios consumidor en la BD")
            return
        consumidor = usuario.consumidor
    except:
        print("❌ Error buscando usuario")
        return
    
    print("📦 Generando 60 ventanas de entrenamiento...")
    print("   - 20 Reposo (Label 0)")
    print("   - 20 Ejercicio (Label 0) [Para evitar falsos positivos]")
    print("   - 20 Ansiedad/Deseo (Label 1) [Target]")
    
    for i in range(20):
        generate_synthetic_window(consumidor, 'rest')
        generate_synthetic_window(consumidor, 'exercise')
        generate_synthetic_window(consumidor, 'craving')
        
        if (i+1) % 5 == 0:
            print(f"   ✅ {i+1} sets creados...")
            
    print(f"✅ Datos insertados exitosamente")

def insert_sample_data_auto():
    print("\n📝 Insertando datos automáticos (Modo CI/CD)...")
    try:
        from api.models import Usuario
        usuario = Usuario.objects.filter(consumidor__isnull=False).first()
        if not usuario:
            return
        consumidor = usuario.consumidor
        
        # Generate balanced dataset
        for _ in range(20):
            generate_synthetic_window(consumidor, 'rest')
            generate_synthetic_window(consumidor, 'exercise')
            generate_synthetic_window(consumidor, 'craving')
            
        print(f"✅ 60 ventanas de entrenamiento generadas")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("🤖 SISTEMA DE ENTRENAMIENTO DE MODELO ML")
    print("="*60)
    
    from api.models import Lectura
    if Lectura.objects.count() == 0:
        print("\n⚠️  No hay datos en la tabla 'lecturas'")
        
        if '--auto' in sys.argv or '-y' in sys.argv:
            print("🔧 Insertando datos automáticamente (flag --auto detectado)...")
            insert_sample_data_auto()
        else:
            insert_sample_data()
    
    success = train_model()
    
    if not success:
        print("\n❌ El entrenamiento falló")
        sys.exit(1)
    
    print("\n✅ Todo listo para usar el sistema de predicción!")

def insert_sample_data_auto():
    print("\n📝 Insertando datos de muestra más realistas...")
    
    from django.utils import timezone
    from django.db import models
    
    try:
        from api.models import Usuario
        usuario = Usuario.objects.filter(consumidor__isnull=False).first()
        if not usuario:
            print("❌ No hay usuarios consumidor en la BD")
            return
        consumidor = usuario.consumidor
        print(f"✅ Usando consumidor: {usuario.email}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("📦 Creando 50 ventanas con patrones variados...")
    
    for i in range(50):
        ventana = Ventana.objects.create(
            consumidor=consumidor,
            window_start=timezone.now(),
            window_end=timezone.now() + timezone.timedelta(minutes=5)
        )
        
        urge_probability = np.random.random()
        is_high_urge = urge_probability > 0.7
        
        for j in range(30):
            if is_high_urge:
                hr_base = np.random.uniform(85, 105)
                hr = np.random.normal(hr_base, 12)
                accel = np.random.normal(1.3, 0.6)
                gyro = np.random.normal(0.7, 0.35)
            else:
                hr_base = np.random.uniform(60, 80)
                hr = np.random.normal(hr_base, 8)
                accel = np.random.normal(0.6, 0.3)
                gyro = np.random.normal(0.25, 0.15)
            
            if np.random.random() < 0.15:
                hr += np.random.uniform(-15, 15)
                accel += np.random.uniform(-0.4, 0.4)
                gyro += np.random.uniform(-0.2, 0.2)
            
            Lectura.objects.create(
                ventana=ventana,
                heart_rate=max(50, min(150, hr)),
                accel_x=accel * np.random.randn(),
                accel_y=accel * np.random.randn(),
                accel_z=accel * np.random.randn(),
                gyro_x=gyro * np.random.randn(),
                gyro_y=gyro * np.random.randn(),
                gyro_z=gyro * np.random.randn()
            )
        
        if is_high_urge:
            prob = np.random.uniform(0.65, 0.95)
        else:
            prob = np.random.uniform(0.05, 0.35)
        
        Analisis.objects.create(
            ventana=ventana,
            probabilidad_modelo=prob,
            urge_label=1 if is_high_urge else 0,
            modelo_usado='manual_label'
        )
        
        if (i + 1) % 10 == 0:
            print(f"   ✅ {i + 1}/50 ventanas creadas...")
    
    print(f"✅ Insertadas 50 ventanas con 1500 lecturas")
    print(f"✅ Insertados 50 análisis para labels")
    print(f"💡 Datos más realistas con overlap y ruido")

