from celery import shared_task
import logging
import numpy as np
import pandas as pd
from datetime import timedelta
from django.db import models
from django.core.cache import cache
from django.utils import timezone
from api.models import Consumidor, Analisis, Ventana, Usuario, Notificacion, Deseo, Lectura

import json
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from api.models import Consumidor, Analisis, Ventana, Usuario, Notificacion, Deseo, Lectura

logger = logging.getLogger(__name__)

def calculate_features_from_readings(consumidor, time_window_minutes=30):
    time_threshold = timezone.now() - timezone.timedelta(minutes=time_window_minutes)
    
    recent_ventanas = Ventana.objects.filter(
        consumidor=consumidor,
        window_start__gte=time_threshold
    ).order_by('-window_start')[:1]
    
    if not recent_ventanas.exists():
        logger.warning(f"No recent ventanas found for consumidor {consumidor.id}")
        return None
    
    ventana = recent_ventanas.first()
    lecturas = Lectura.objects.filter(ventana=ventana)
    
    if not lecturas.exists():
        logger.warning(f"No lecturas found in ventana {ventana.id}")
        return None
    
    heart_rates = [l.heart_rate or 0 for l in lecturas]
    accel_x = [l.accel_x or 0 for l in lecturas]
    accel_y = [l.accel_y or 0 for l in lecturas]
    accel_z = [l.accel_z or 0 for l in lecturas]
    gyro_x = [l.gyro_x or 0 for l in lecturas]
    gyro_y = [l.gyro_y or 0 for l in lecturas]
    gyro_z = [l.gyro_z or 0 for l in lecturas]
    
    hr_array = np.array(heart_rates)
    
    accel_magnitude = np.sqrt(
        np.array(accel_x)**2 + 
        np.array(accel_y)**2 + 
        np.array(accel_z)**2
    )
    
    gyro_magnitude = np.sqrt(
        np.array(gyro_x)**2 + 
        np.array(gyro_y)**2 + 
        np.array(gyro_z)**2
    )
    
    features = {
        'hr_mean': float(np.mean(hr_array)),
        'hr_std': float(np.std(hr_array)),
        'hr_min': float(np.min(hr_array)),
        'hr_max': float(np.max(hr_array)),
        'hr_range': float(np.max(hr_array) - np.min(hr_array)),
        'accel_magnitude_mean': float(np.mean(accel_magnitude)),
        'accel_magnitude_std': float(np.std(accel_magnitude)),
        'gyro_magnitude_mean': float(np.mean(gyro_magnitude)),
        'gyro_magnitude_std': float(np.std(gyro_magnitude)),
        'accel_energy': float(np.sum(np.array(accel_x)**2 + np.array(accel_y)**2 + np.array(accel_z)**2)),
        'gyro_energy': float(np.sum(np.array(gyro_x)**2 + np.array(gyro_y)**2 + np.array(gyro_z)**2)),
    }
    
    return features, ventana

@shared_task(bind=True, max_retries=3)
def predict_smoking_craving(self, user_id, features_dict=None):
    try:
        logger.info(f"Starting prediction for user {user_id}")
        
        try:
            usuario = Usuario.objects.get(id=user_id)
        except Usuario.DoesNotExist:
            error_msg = f"Usuario {user_id} does not exist"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        
        try:
            consumidor = usuario.consumidor
        except Consumidor.DoesNotExist:
            error_msg = f"Usuario {user_id} has no linked Consumidor record"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'user_id': user_id,
                'user_email': usuario.email,
                'suggestion': 'Create a Consumidor record for this Usuario'
            }
        
        logger.info(f"Received features_dict: {features_dict}")
        logger.info(f"features_dict is None: {features_dict is None}")
        logger.info(f"features_dict type: {type(features_dict)}")
        
        if features_dict is None or len(features_dict) == 0 or 'hr_mean' not in features_dict:
            logger.info(f"Calculating features from sensor readings for consumidor {consumidor.id}")
            result = calculate_features_from_readings(consumidor)
            
            if result is None:
                error_msg = "No recent sensor readings found. Cannot make prediction."
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'suggestion': 'Ensure wearable is sending sensor data (Lectura records)'
                }
            
            features_dict, existing_ventana = result
            logger.info(f"Features calculated: {features_dict}")
        else:
            logger.info(f"Using provided manual features")
            existing_ventana = None
        
        try:
            import joblib
            
            model_package = cache.get('ml_model_package')
            if model_package is None:
                model_package = joblib.load('models/smoking_craving_model.pkl')
                cache.set('ml_model_package', model_package, timeout=3600)
            
            model = model_package['model']
            scaler = model_package['scaler']
            feature_names = model_package['feature_names']
            
        except FileNotFoundError:
            error_msg = "ML model file not found at 'models/smoking_craving_model.pkl'"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'suggestion': 'Train and save your ML model first'
            }
        except KeyError as e:
            error_msg = f"Model package missing key: {e}. Retrain the model."
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return {
                'success': False,
                'error': f'Model loading failed: {str(e)}'
            }
        
        features_df = pd.DataFrame([features_dict])
        
        try:
            features_df = features_df[feature_names]
        except KeyError as e:
            error_msg = f"Missing required features: {e}. Required: {feature_names}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        
        features_scaled = scaler.transform(features_df)
        
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0][1]
        
        model_metrics = model_package.get('metrics', {})
        accuracy = model_metrics.get('accuracy')
        precision = model_metrics.get('precision')
        recall = model_metrics.get('recall')
        f1 = model_metrics.get('f1_score')
        if probability >= 0.7:
            risk_level = 'high'
            comentario = f'Alto riesgo de deseo detectado ({probability*100:.1f}%). Intervención inmediata recomendada.'
        elif probability >= 0.4:
            risk_level = 'medium'
            comentario = f'Riesgo moderado de deseo ({probability*100:.1f}%). Monitoreo continuo recomendado.'
        else:
            risk_level = 'low'
            comentario = f'Bajo riesgo de deseo ({probability*100:.1f}%). Estado estable.'
        
        logger.info(f"Prediction: probability={probability:.2%}, risk={risk_level}")
        
        if existing_ventana:
            ventana = existing_ventana
        else:
            ventana = Ventana.objects.create(
                consumidor=consumidor,
                window_start=timezone.now(),
                window_end=timezone.now() + timezone.timedelta(minutes=30)
            )
        
        ventana.hr_mean = features_dict.get('hr_mean')
        ventana.hr_std = features_dict.get('hr_std')
        ventana.accel_energy = features_dict.get('accel_energy')
        ventana.gyro_energy = features_dict.get('gyro_energy')
        ventana.save()
        
        logger.info(f"Features saved to Ventana ID {ventana.id}")
        
        analisis = Analisis.objects.create(
            ventana=ventana,
            probabilidad_modelo=float(probability),
            urge_label=int(prediction),
            modelo_usado='LogisticRegression_v1',
            recall=recall,
            f1_score=f1,
            accuracy=accuracy,
            roc_auc=None,
            comentario_modelo=comentario
        )
        
        logger.info(f"Prediction saved: Analisis ID {analisis.id}, risk={risk_level}, prob={probability:.2%}")
        
        if risk_level == 'high':
            deseo = Deseo.objects.create(
                consumidor=consumidor,
                ventana=ventana,
                tipo='sustancia',
                resolved=False
            )
            
            Notificacion.objects.create(
                consumidor=consumidor,
                deseo=deseo,
                contenido=comentario,
                tipo='alerta',
                leida=False
            )
            
            logger.info(f"High risk notification created for consumidor {consumidor.id}")
        
        return {
            'success': True,
            'analisis_id': analisis.id,
            'probability': float(probability),
            'prediction': int(prediction),
            'risk_level': risk_level,
            'comentario': comentario,
            'model_metrics': {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            },
            'user_id': user_id,
            'consumidor_id': consumidor.id
        }
        
    except Exception as exc:
        logger.error(f"Unexpected error in prediction: {exc}")
        if isinstance(exc, (Usuario.DoesNotExist, Consumidor.DoesNotExist)):
            return {
                'success': False,
                'error': str(exc)
            }
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task(bind=True, max_retries=2)
def simulate_wearable_cycle(self, ventana_id=None):
    """
    Simulates wearable sensor data.
    Solo genera datos para consumidores con is_simulating=True
    
    Args:
        ventana_id (int, optional): If provided, generates data for this SPECIFIC window (User Session).
                                    If None, picks a random consumer (Legacy/Demo mode).
    """
    import random
    from datetime import timedelta
    
    logger.info("=" * 70)
    logger.info(f"[CYCLE] Iniciando ciclo de simulación (Target Ventana: {ventana_id})")
    
    try:
        if ventana_id:
            # TARGETED MODE: Generate data for specific user session
            try:
                ventana = Ventana.objects.get(id=ventana_id)
                consumidor = ventana.consumidor
                usuario = consumidor.usuario
                
                # ✅ VERIFICAR SI LA SIMULACIÓN ESTÁ ACTIVADA
                if not consumidor.is_simulating:
                    logger.info(f"[SKIP] Simulación DESACTIVADA para consumidor {consumidor.id}")
                    return {
                        'success': False, 
                        'error': 'Simulation disabled for this consumer',
                        'consumidor_id': consumidor.id
                    }
                
                logger.info(f"[TARGET] Generando datos para Usuario: {usuario.email}")
            except Ventana.DoesNotExist:
                logger.error(f"[ERROR] Ventana {ventana_id} no existe. Abortando.")
                return {'success': False, 'error': 'Ventana not found'}
        else:
            # LEGACY MODE: Solo consumidores con simulación ACTIVADA
            consumidores = list(
                Consumidor.objects.filter(is_simulating=True)
                .select_related('usuario')
            )
            
            if not consumidores:
                logger.info("[SKIP] No hay consumidores con simulación activa")
                return {
                    'success': False, 
                    'error': 'No consumers with simulation enabled'
                }
            
            consumidor = random.choice(consumidores)
            usuario = consumidor.usuario
            
            now = timezone.now()
            ventana = Ventana.objects.create(
                consumidor=consumidor,
                window_start=now - timedelta(minutes=1),
                window_end=now
            )
            logger.info(f"[LEGACY] Ventana aleatoria creada: {ventana.id}")

        # Generate realistic data patterns
        # 10% chance of "Craving" pattern (High HR + Low Motion)
        is_craving = random.random() < 0.10
        
        if is_craving:
            base_hr = random.uniform(85, 100) # Elevated HR
            motion_factor = 0.1 # Low motion
            logger.info("[PATTERN] Simulating CRAVING (High HR, Low Motion)")
        else:
            base_hr = random.uniform(65, 80) # Normal HR
            motion_factor = 1.0 # Normal motion
            
        lecturas_creadas = 0
        # Generate 12 readings (assuming 5-second interval call, this creates a burst)
        # Or if called frequently, maybe just 1 reading? 
        # Let's generate a small batch (e.g., 5 seconds worth of data at 1Hz = 5 readings)
        
        for i in range(5):
            hr = base_hr + random.uniform(-3, 3)
            
            accel_x = random.uniform(-1.0, 1.0) * motion_factor
            accel_y = random.uniform(-1.0, 1.0) * motion_factor
            accel_z = random.uniform(-1.0, 1.0) * motion_factor
            
            gyro_x = random.uniform(-0.5, 0.5) * motion_factor
            gyro_y = random.uniform(-0.5, 0.5) * motion_factor
            gyro_z = random.uniform(-0.5, 0.5) * motion_factor
            
            Lectura.objects.create(
                ventana=ventana,
                heart_rate=max(50, min(150, hr)),
                accel_x=accel_x, accel_y=accel_y, accel_z=accel_z,
                gyro_x=gyro_x, gyro_y=gyro_y, gyro_z=gyro_z
            )
            lecturas_creadas += 1
        
        logger.info(f"[OK] {lecturas_creadas} lecturas generadas para Ventana {ventana.id}")
        
        # Trigger prediction
        predict_smoking_craving.apply_async(
            kwargs={'user_id': usuario.id, 'features_dict': None},
            countdown=1
        )
        
        return {
            'success': True,
            'ventana_id': ventana.id,
            'lecturas': lecturas_creadas,
            'pattern': 'craving' if is_craving else 'normal'
        }
        
    except Exception as exc:
        logger.error(f"[ERROR] Error en ciclo de simulación: {exc}")
        return {'success': False, 'error': str(exc)}

@shared_task(bind=True)
def check_sensor_activity(self, user_id, ventana_id):
    """
    Checks if sensor data is being received. If not, starts synthetic generator.
    """
    logger.info(f"[CHECK] Verificando actividad de sensores para Ventana {ventana_id}")
    
    try:
        # Check if any readings exist for this window
        readings_count = Lectura.objects.filter(ventana_id=ventana_id).count()
        
        if readings_count == 0:
            logger.warning(f"[ALERT] No data received for Ventana {ventana_id}. Starting BACKUP GENERATOR.")
            
            # Get or create 5-second schedule
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=5,
                period=IntervalSchedule.SECONDS,
            )
            
            # Create dynamic periodic task
            task_name = f"synthetic_data_user_{user_id}"
            
            PeriodicTask.objects.update_or_create(
                name=task_name,
                defaults={
                    'interval': schedule,
                    'task': 'api.tasks.simulate_wearable_cycle',
                    'args': json.dumps([]),
                    'kwargs': json.dumps({'ventana_id': ventana_id}),
                    'enabled': True
                }
            )
            logger.info(f"[SUCCESS] Backup generator started: {task_name}")
            return "Backup generator started"
            
        else:
            logger.info(f"[OK] Data detected ({readings_count} readings). No backup needed.")
            return "Data detected"
            
    except Exception as e:
        logger.error(f"[ERROR] Failed to check sensor activity: {e}")
        return f"Error: {e}"

@shared_task(bind=True)
def stop_synthetic_generation(self, user_id):
    """
    Stops the synthetic data generator for a user.
    """
    task_name = f"synthetic_data_user_{user_id}"
    try:
        deleted_count, _ = PeriodicTask.objects.filter(name=task_name).delete()
        if deleted_count > 0:
            logger.info(f"[STOP] Backup generator stopped for User {user_id}")
        else:
            logger.info(f"[STOP] No active generator found for User {user_id}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to stop generator: {e}")


@shared_task(bind=True, max_retries=3)
def calculate_ventana_statistics(self, ventana_id):
    """
    Calculate aggregated statistics for a ventana based on its lecturas
    Called periodically or when enough readings have accumulated
    
    This calculates:
    - hr_mean: Average heart rate
    - hr_std: Heart rate standard deviation
    - accel_energy: Total accelerometer energy (movement intensity)
    - gyro_energy: Total gyroscope energy (rotation intensity)
    """
    try:
        logger.info(f"[VENTANA-CALC] Starting calculation for Ventana {ventana_id}")
        
        # Get the ventana
        try:
            ventana = Ventana.objects.get(id=ventana_id)
        except Ventana.DoesNotExist:
            logger.error(f"[VENTANA-CALC] Ventana {ventana_id} not found")
            return {
                'success': False,
                'error': f'Ventana {ventana_id} does not exist'
            }
        
        # Get all lecturas for this ventana
        lecturas = Lectura.objects.filter(ventana=ventana).order_by('created_at')
        
        if not lecturas.exists():
            logger.warning(f"[VENTANA-CALC] No lecturas found for Ventana {ventana_id}")
            return {
                'success': False,
                'error': 'No sensor readings available',
                'ventana_id': ventana_id
            }
        
        lectura_count = lecturas.count()
        logger.info(f"[VENTANA-CALC] Processing {lectura_count} readings")
        
        # Extract sensor data
        heart_rates = []
        accel_x_values = []
        accel_y_values = []
        accel_z_values = []
        gyro_x_values = []
        gyro_y_values = []
        gyro_z_values = []
        
        for lectura in lecturas:
            if lectura.heart_rate is not None:
                heart_rates.append(lectura.heart_rate)
            
            if lectura.accel_x is not None:
                accel_x_values.append(lectura.accel_x)
            if lectura.accel_y is not None:
                accel_y_values.append(lectura.accel_y)
            if lectura.accel_z is not None:
                accel_z_values.append(lectura.accel_z)
            
            if lectura.gyro_x is not None:
                gyro_x_values.append(lectura.gyro_x)
            if lectura.gyro_y is not None:
                gyro_y_values.append(lectura.gyro_y)
            if lectura.gyro_z is not None:
                gyro_z_values.append(lectura.gyro_z)
        
        # Calculate heart rate statistics
        if heart_rates:
            hr_array = np.array(heart_rates)
            ventana.hr_mean = float(np.mean(hr_array))
            ventana.hr_std = float(np.std(hr_array))
            logger.info(f"[HR-STATS] Mean: {ventana.hr_mean:.2f}, Std: {ventana.hr_std:.2f}")
        else:
            logger.warning(f"[VENTANA-CALC] No heart rate data available")
        
        # Calculate accelerometer energy (movement intensity)
        if accel_x_values and accel_y_values and accel_z_values:
            accel_x_array = np.array(accel_x_values)
            accel_y_array = np.array(accel_y_values)
            accel_z_array = np.array(accel_z_values)
            
            # Energy = sum of squared values
            ventana.accel_energy = float(
                np.sum(accel_x_array**2 + accel_y_array**2 + accel_z_array**2)
            )
            
            logger.info(f"[ACCEL-ENERGY] {ventana.accel_energy:.4f}")
        else:
            logger.warning(f"[VENTANA-CALC] No accelerometer data available")
        
        # Calculate gyroscope energy (rotation intensity)
        if gyro_x_values and gyro_y_values and gyro_z_values:
            gyro_x_array = np.array(gyro_x_values)
            gyro_y_array = np.array(gyro_y_values)
            gyro_z_array = np.array(gyro_z_values)
            
            # Energy = sum of squared values
            ventana.gyro_energy = float(
                np.sum(gyro_x_array**2 + gyro_y_array**2 + gyro_z_array**2)
            )
            
            logger.info(f"[GYRO-ENERGY] {ventana.gyro_energy:.4f}")
        else:
            logger.warning(f"[VENTANA-CALC] No gyroscope data available")
        
        # Save the calculated statistics
        ventana.save()
        
        logger.info(
            f"[VENTANA-CALC] ✓ Successfully calculated statistics for Ventana {ventana_id}"
        )
        
        return {
            'success': True,
            'ventana_id': ventana_id,
            'lecturas_processed': lectura_count,
            'statistics': {
                'hr_mean': ventana.hr_mean,
                'hr_std': ventana.hr_std,
                'accel_energy': ventana.accel_energy,
                'gyro_energy': ventana.gyro_energy
            }
        }
        
    except Exception as exc:
        logger.error(f"[VENTANA-CALC] Error calculating statistics: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True)
def check_and_calculate_ventana_stats(self, ventana_id, min_readings=5):
    """
    Check if a ventana has enough readings and trigger calculation
    
    Args:
        ventana_id: ID of the ventana to check
        min_readings: Minimum number of readings before calculating (default: 5)
    """
    try:
        ventana = Ventana.objects.get(id=ventana_id)
        lectura_count = Lectura.objects.filter(ventana=ventana).count()
        
        logger.info(
            f"[CHECK-CALC] Ventana {ventana_id} has {lectura_count} readings "
            f"(min: {min_readings})"
        )
        
        if lectura_count >= min_readings:
            # Trigger calculation
            logger.info(f"[CHECK-CALC] Triggering calculation for Ventana {ventana_id}")
            calculate_ventana_statistics.delay(ventana_id)
            
            return {
                'success': True,
                'ventana_id': ventana_id,
                'lectura_count': lectura_count,
                'action': 'calculation_triggered'
            }
        else:
            logger.info(
                f"[CHECK-CALC] Not enough readings yet for Ventana {ventana_id} "
                f"({lectura_count}/{min_readings})"
            )
            return {
                'success': True,
                'ventana_id': ventana_id,
                'lectura_count': lectura_count,
                'action': 'waiting_for_more_data'
            }
            
    except Ventana.DoesNotExist:
        logger.error(f"[CHECK-CALC] Ventana {ventana_id} not found")
        return {
            'success': False,
            'error': f'Ventana {ventana_id} does not exist'
        }


@shared_task(bind=True)
def periodic_ventana_calculation(self):
    """
    Periodic task to create and process 5-minute sliding windows
    Run this EVERY 5 MINUTES via Celery Beat
    
    For each active consumer (with active session):
    1. Create a new 5-minute ventana
    2. Move lecturas from previous ventana to new ventana if needed
    3. Calculate statistics for completed ventanas
    4. Trigger ML predictions
    """
    try:
        logger.info("[PERIODIC-5MIN] Starting 5-minute ventana cycle")
        
        now = timezone.now()
        five_minutes_ago = now - timedelta(minutes=5)
        
        # Get all consumers with active sessions (logged in recently)
        # Check cache for active sessions
        from django.core.cache import cache
        
        # Get all consumidores with active monitoring sessions
        active_sessions = []
        for key in cache.keys('active_session:*'):
            session_data = cache.get(key)
            if session_data:
                active_sessions.append(session_data['consumidor_id'])
        
        if not active_sessions:
            logger.info("[PERIODIC-5MIN] No active consumer sessions found")
            return {
                'success': True,
                'message': 'No active sessions'
            }
        
        logger.info(f"[PERIODIC-5MIN] Processing {len(active_sessions)} active consumers")
        
        ventanas_created = 0
        ventanas_calculated = 0
        predictions_triggered = 0
        
        for consumidor_id in active_sessions:
            try:
                consumidor = Consumidor.objects.get(id=consumidor_id)
                usuario = consumidor.usuario
                
                # Get the current active ventana for this consumer
                current_ventana = Ventana.objects.filter(
                    consumidor=consumidor,
                    window_end__gt=now  # Still active
                ).order_by('-window_start').first()
                
                if not current_ventana:
                    logger.warning(f"[PERIODIC-5MIN] No active ventana for consumer {consumidor_id}")
                    continue
                
                # Check if it's time to close this window and create a new one
                # Windows are 5 minutes long
                window_duration = (now - current_ventana.window_start).total_seconds() / 60
                
                if window_duration >= 5:
                    logger.info(
                        f"[PERIODIC-5MIN] Closing ventana {current_ventana.id} "
                        f"for consumer {consumidor_id} (duration: {window_duration:.1f}min)"
                    )
                    
                    # 1. Calculate statistics for the completed window
                    lectura_count = Lectura.objects.filter(ventana=current_ventana).count()
                    
                    if lectura_count >= 5:  # Minimum readings for valid stats
                        logger.info(
                            f"[PERIODIC-5MIN] Calculating stats for ventana {current_ventana.id} "
                            f"({lectura_count} readings)"
                        )
                        
                        # Calculate statistics synchronously (it's fast)
                        result = calculate_ventana_statistics.apply_async(
                            args=[current_ventana.id]
                        ).get(timeout=10)
                        
                        if result.get('success'):
                            ventanas_calculated += 1
                            
                            # Send WebSocket update for heart rate data
                            try:
                                from channels.layers import get_channel_layer
                                from asgiref.sync import async_to_sync
                                
                                channel_layer = get_channel_layer()
                                
                                # Refresh ventana to get calculated values
                                current_ventana.refresh_from_db()
                                
                                async_to_sync(channel_layer.group_send)(
                                    f'heart_rate_{consumidor_id}',
                                    {
                                        'type': 'hr_update',
                                        'data': {
                                            'ventana_id': current_ventana.id,
                                            'window_start': current_ventana.window_start.isoformat(),
                                            'window_end': current_ventana.window_end.isoformat(),
                                            'hr_mean': float(current_ventana.hr_mean) if current_ventana.hr_mean else None,
                                            'hr_std': float(current_ventana.hr_std) if current_ventana.hr_std else None,
                                        }
                                    }
                                )
                                logger.debug(f"💓 WebSocket HR update sent for ventana {current_ventana.id}")
                            except Exception as ws_error:
                                logger.warning(f"Failed to send WebSocket HR update: {ws_error}")
                            
                            # 2. Trigger ML prediction
                            logger.info(
                                f"[PERIODIC-5MIN] Triggering prediction for "
                                f"user {usuario.id}, ventana {current_ventana.id}"
                            )
                            
                            predict_smoking_craving.delay(usuario.id, features_dict=None)
                            predictions_triggered += 1
                    else:
                        logger.warning(
                            f"[PERIODIC-5MIN] Not enough readings for ventana {current_ventana.id} "
                            f"({lectura_count} < 5)"
                        )
                    
                    # 3. Create new 5-minute window
                    new_ventana = Ventana.objects.create(
                        consumidor=consumidor,
                        window_start=now,
                        window_end=now + timedelta(minutes=5)
                    )
                    
                    ventanas_created += 1
                    
                    logger.info(
                        f"[PERIODIC-5MIN] Created new ventana {new_ventana.id} "
                        f"for consumer {consumidor_id}"
                    )
                    
                    # Update session cache with new ventana
                    session_key = f'active_session:{consumidor_id}'
                    session_data = cache.get(session_key)
                    if session_data:
                        session_data['ventana_id'] = new_ventana.id
                        cache.set(session_key, session_data, timeout=28800)
                        
                        # Also update device session
                        device_key = f"device_session:{session_data.get('device_id', 'default')}"
                        device_data = cache.get(device_key)
                        if device_data:
                            device_data['ventana_id'] = new_ventana.id
                            cache.set(device_key, device_data, timeout=28800)
                
            except Consumidor.DoesNotExist:
                logger.error(f"[PERIODIC-5MIN] Consumidor {consumidor_id} not found")
                continue
            except Exception as e:
                logger.error(
                    f"[PERIODIC-5MIN] Error processing consumer {consumidor_id}: {e}"
                )
                continue
        
        logger.info(
            f"[PERIODIC-5MIN] ✓ Cycle complete: "
            f"{ventanas_created} created, {ventanas_calculated} calculated, "
            f"{predictions_triggered} predictions triggered"
        )
        
        return {
            'success': True,
            'ventanas_created': ventanas_created,
            'ventanas_calculated': ventanas_calculated,
            'predictions_triggered': predictions_triggered,
            'active_consumers': len(active_sessions)
        }
        
    except Exception as exc:
        logger.error(f"[PERIODIC-5MIN] Error in periodic calculation: {exc}")
        return {
            'success': False,
            'error': str(exc)
        }


@shared_task(bind=True)
def trigger_prediction_if_ready(self, ventana_id):
    """
    Check if ventana has calculated statistics and trigger ML prediction
    This should be called after calculate_ventana_statistics completes
    """
    try:
        ventana = Ventana.objects.get(id=ventana_id)
        
        # Check if statistics are calculated
        if (ventana.hr_mean is not None and 
            ventana.accel_energy is not None and 
            ventana.gyro_energy is not None):
            
            logger.info(
                f"[PREDICTION-TRIGGER] Ventana {ventana_id} ready for prediction"
            )
            
            # Get the consumidor and usuario
            consumidor = ventana.consumidor
            usuario = consumidor.usuario
            
            # Prepare features for prediction
            features = {
                'hr_mean': ventana.hr_mean,
                'hr_std': ventana.hr_std,
                'accel_energy': ventana.accel_energy,
                'gyro_energy': ventana.gyro_energy,
            }
            
            # Trigger prediction task
            from api.tasks import predict_smoking_craving
            predict_smoking_craving.delay(usuario.id, features)
            
            logger.info(f"[PREDICTION-TRIGGER] ✓ Prediction triggered for User {usuario.id}")
            
            return {
                'success': True,
                'ventana_id': ventana_id,
                'user_id': usuario.id,
                'action': 'prediction_triggered'
            }
        else:
            logger.warning(
                f"[PREDICTION-TRIGGER] Ventana {ventana_id} not ready - "
                f"statistics incomplete"
            )
            return {
                'success': False,
                'ventana_id': ventana_id,
                'error': 'Statistics not calculated yet'
            }
            
    except Ventana.DoesNotExist:
        logger.error(f"[PREDICTION-TRIGGER] Ventana {ventana_id} not found")
        return {
            'success': False,
            'error': f'Ventana {ventana_id} does not exist'
        }
    except Exception as exc:
        logger.error(f"[PREDICTION-TRIGGER] Error: {exc}")
        return {
            'success': False,
            'error': str(exc)
        }
