/*
 * Прошивка для Arduino для сбора данных ЭЭГ
 * Читает аналоговые сигналы и отправляет через Serial порт
 */

#define EEG_PIN A0          // Пин для сигнала ЭЭГ
#define SAMPLE_RATE 50       // Частота дискретизации (Гц)
#define SERIAL_BAUD 115200   // Скорость передачи данных

// Калибровочные коэффициенты (нужно настроить под ваше оборудование)
#define ADC_TO_MICROVOLTS 0.488  // Коэффициент преобразования ADC -> мкВ
#define BASELINE_OFFSET 512       // Базовое смещение ADC (для 10-бит ADC)

unsigned long lastSampleTime = 0;
unsigned long sampleInterval = 1000000 / SAMPLE_RATE; // Интервал между сэмплами в микросекундах

void setup() {
    // Настройка Serial порта
    Serial.begin(SERIAL_BAUD);

    // Настройка пина ЭЭГ
    pinMode(EEG_PIN, INPUT);

    // Короткая задержка для стабилизации
    delay(100);

    // Отправка приветственного сообщения
    Serial.println("EEG Arduino Ready");
    Serial.println("Format: float_value");
}

void loop() {
    unsigned long currentTime = micros();

    // Проверяем, прошло ли достаточно времени для следующего сэмпла
    if (currentTime - lastSampleTime >= sampleInterval) {
        lastSampleTime = currentTime;

        // Читаем значение с АЦП
        int adcValue = analogRead(EEG_PIN);

        // Преобразуем в микровольты с учетом смещения
        float microvolts = (adcValue - BASELINE_OFFSET) * ADC_TO_MICROVOLTS;

        // Отправляем значение через Serial
        // Формат: просто число с плавающей точкой, заканчивается новой строкой
        Serial.println(microvolts, 3);  // 3 знака после запятой
    }
}