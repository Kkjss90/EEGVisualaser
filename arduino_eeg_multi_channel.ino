/*
 * Расширенная прошивка для Arduino для многоканального сбора данных ЭЭГ
 * Поддерживает до 6 каналов + опорный электрод
 */

#define NUM_CHANNELS 4      // Количество каналов ЭЭГ
#define EEG_PINS {A0, A1, A2, A3}  // Пины для каналов
#define REF_PIN A4          // Опорный электрод (если используется)
#define SAMPLE_RATE 50      // Частота дискретизации (Гц)
#define SERIAL_BAUD 115200  // Скорость передачи

// Калибровочные коэффициенты
#define ADC_TO_MICROVOLTS 0.488
#define BASELINE_OFFSET 512

const int eegPins[NUM_CHANNELS] = EEG_PINS;
unsigned long lastSampleTime = 0;
unsigned long sampleInterval = 1000000 / SAMPLE_RATE;

void setup() {
    Serial.begin(SERIAL_BAUD);

    // Настройка пинов
    for(int i = 0; i < NUM_CHANNELS; i++) {
        pinMode(eegPins[i], INPUT);
    }
    pinMode(REF_PIN, INPUT);

    delay(100);

    Serial.println("Multi-Channel EEG Arduino Ready");
    Serial.print("Channels: ");
    Serial.println(NUM_CHANNELS);
    Serial.println("Format: ch1,ch2,ch3,ch4");
}

void loop() {
    unsigned long currentTime = micros();

    if (currentTime - lastSampleTime >= sampleInterval) {
        lastSampleTime = currentTime;

        // Читаем опорный электрод (если используется)
        int refValue = analogRead(REF_PIN);

        // Читаем все каналы
        for(int i = 0; i < NUM_CHANNELS; i++) {
            int adcValue = analogRead(eegPins[i]);

            // Вычитаем опорный сигнал для лучшего качества
            float microvolts = (adcValue - refValue) * ADC_TO_MICROVOLTS;

            // Отправляем значение
            Serial.print(microvolts, 2);

            // Разделитель между каналами
            if(i < NUM_CHANNELS - 1) {
                Serial.print(",");
            }
        }

        Serial.println();  // Новая строка в конце
    }
}