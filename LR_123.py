import random
import secrets

# ЛР1 Генераация подстановки
def generate():
    elements = list(range(64))
    # Алгоритм Фишера-Йетсa
    for i in range(len(elements) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        elements[i], elements[j] = elements[j], elements[i]
    return elements

# ЛР1 Векторы
def VecOfVal(g_x):
    for i in range(64):
        x_bin = format(i, "06b")
        g_bin = format(g_x[i], "06b")

        x1, x2, x3, x4, x5, x6 = [int(b) for b in x_bin]
        f1, f2, f3, f4, f5, f6 = [int(b) for b in g_bin]
        
        print(f"{x1}  {x2}  {x3}  {x4}  {x5}  {x6}  |  {g_x[i]:3d}  |  {f1}  {f2}  {f3}  {f4}  {f5}  {f6}")

# ЛР1 Вес Хэмминга
def hamming_weight(g_x):
    # Инициализируем счетчики для f1...f6
    weights = [0, 0, 0, 0, 0, 0]
    for i in range(64):
        g_bin = format(g_x[i], "06b")
        bits = [int(b) for b in g_bin]  # [f1, f2, f3, f4, f5, f6]
        
        # Увеличиваем веса для каждой координатной функции
        for k in range(6):
            weights[k] += bits[k]

        #print(weights)
        
    return weights

# ЛР1 Мн-н Жегалкина
def mobius(f):
    # Быстрое преобразование Мёбиуса (XOR-БПФ)
    res = f[:]
    for i in range(6):
        step = 1 << i
        for j in range(0, 64, step << 1):
            for k in range(j, j + step):
                res[k + step] ^= res[k]
    return res

def mask_to_term(mask):
    # Маска → терм (например, 3 → 'x5x6')
    if mask == 0:
        return "1"
    return ''.join(f"x{i+1}" for i in range(6) if (mask >> (5 - i)) & 1)

def anf_to_polynomial(anf):
    # Коэффициенты АНФ → полином
    terms = [mask_to_term(m) for m, c in enumerate(anf) if c == 1]
    return " ⊕ ".join(terms) if terms else "0"

def compute_zhegalkin(g, verbose=False):
    # Вычисляет полиномы Жегалкина для всех 6 координатных функций
    # Строим таблицы истинности
    tables = [[(val >> (5 - j)) & 1 for val in g] for j in range(6)]
    
    if verbose:
        print("Многочлены Жегалкина: ")
    
    for j, table in enumerate(tables):
        anf = mobius(table)
        poly = anf_to_polynomial(anf)
        print(f"f{j+1} = {poly}\n")

# ЛР1 Фиктивные переменные
def find_dummy_in_polynomial(anf_coeffs):
    # Поиск фиктивных переменных по коэффициентам АНФ
    used = set()
    for mask, coeff in enumerate(anf_coeffs):
        if coeff and mask:
            for i in range(6):
                if (mask >> (5 - i)) & 1:
                    used.add(i + 1)
    return [i for i in range(1, 7) if i not in used]

def analyze_all(g):
    tables = [[(val >> (5 - j)) & 1 for val in g] for j in range(6)]

    print("Фиктивные переменные")
    
    for j, table in enumerate(tables):
        anf = mobius(table)
        dummy = find_dummy_in_polynomial(anf)
        
        status = f"фиктивные: {dummy}" if dummy else "нет фиктивных"
        print(f"f_{j+1}: {status}")
        
        if not dummy:
            print(f"  Все 6 переменных существенны")

# ЛР2 Сбалансированность
# d(f) = |wt(f) - 2^(n-1)|
# eps(f) = d(f) / 2^(n-1) = |wt(f) - 32| / 32
def calculate_balance(weights):
    # biases: список преобладаний d(f_k)
    # normalized: список нормированных преобладаний eps(f_k)
    n = 6
    half = 2 ** (n - 1)  # 32
    biases = []
    normalized = []
    
    for w in weights:
        d = abs(w - half)
        epsilon = d / half
        biases.append(d)
        normalized.append(epsilon)
    
    return biases, normalized

def print_balance_analysis(weights):
    biases, normalized = calculate_balance(weights)
    
    print("\nОценка сбалансированности координатных функций")
    print(f"\nТеоретически сбалансированная функция: wt = 32, d = 0, eps = 0\n")
        
    for k in range(6):
        w = weights[k]
        d = biases[k]
        eps = normalized[k]
        
        print(f"│  f_{k+1}  │     {w:2d}     │     {d:2d}     │  {eps:6.4f} │")

# ЛР2 Сильная равновероятность
def is_k_balanced(func, k):
    """
    Параметры:
        func: список из 64 значений (таблица истинности функции)
        k: количество фиксируемых переменных (1..6)
    Возвращает:
        True если функция k-равновероятна, иначе False
    """
    n = 6
    group_size = 1 << (n - k)  # 2^(6-k) — сколько наборов в группе
    
    for mask in range(1 << k):  # перебираем все варианты первых k бит
        ones = 0
        zeros = 0
        
        # Перебираем все варианты оставшихся (n-k) бит
        for rest in range(1 << (n - k)):
            # Формируем индекс: (mask << (n-k)) | rest
            idx = (mask << (n - k)) | rest
            if func[idx] == 1:
                ones += 1
            else:
                zeros += 1
        
        if ones != group_size // 2 or zeros != group_size // 2:
            return False
    
    return True


def is_strongly_balanced(func):
    """
    Проверяет, является ли функция сильно-равновероятной.
    """
    for k in range(1, 7):
        if not is_k_balanced(func, k):
            return False, k
    return True, None


def analyze_strong_balance(g):
    # Анализирует свойство сильной равновероятности для всех 6 координатных функций.
    # Строим таблицы истинности
    tables = [[(val >> (5 - j)) & 1 for val in g] for j in range(6)]

    print("\nСильно-равновероятность")

    for j, table in enumerate(tables):
        is_strong, fail_k = is_strongly_balanced(table)
        
        if is_strong:
            print(f"f_{j+1}: СИЛЬНО-РАВНОВЕРОЯТНА")
        else:
            print(f"f_{j+1}: НЕ сильно-равновероятна (нарушена {fail_k}-равновероятность)")

# ЛР2 Поиск запрещённых последовательностей
def find_forbidden_sequence(func, k):
    """
    Параметры:
        func: таблица истинности (64 значения)
        k: длина последовательности
    Возвращает:
        (first_k, pattern) - первый блок и запрещённый паттерн
        или (None, None) если запретов нет
    """
    n = 6
    group_size = 1 << (n - k)  # количество выходов для фиксированного first_k
    
    for first_k in range(1 << k):
        # Собираем выходные биты для данного first_k
        output_bits = []
        for rest in range(1 << (n - k)):
            idx = (first_k << (n - k)) | rest
            output_bits.append(func[idx])
        
        # Преобразуем в строку
        output_str = ''.join(str(b) for b in output_bits)
        
        # Проверяем все возможные паттерны длины k
        for pattern_int in range(1 << k):
            pattern = format(pattern_int, f'0{k}b')
            if pattern not in output_str:
                return first_k, pattern
    
    return None, None


def find_all_forbidden_sequences(g):
    """
    Находит запрещённые последовательности для всех координатных функций.
    """
    tables = [[(val >> (5 - j)) & 1 for val in g] for j in range(6)]

    print("\nПОИСК ЗАПРЕЩЁННЫХ ПОСЛЕДОВАТЕЛЬНОСТЕЙ (при фиксации k бит)")

    
    for j, table in enumerate(tables):
        is_strong, fail_k = is_strongly_balanced(table)
        
        if is_strong:
            print(f"f_{j+1}: сильно-равновероятна → запретов нет")
        else:
            # Ищем запрет для k, на котором нарушена равновероятность
            first_k, forbidden = find_forbidden_sequence(table, fail_k)
            if forbidden:
                first_k_bits = format(first_k, f'0{fail_k}b')
                print(f"f_{j+1}: найден запрет длины {fail_k}: '{forbidden}'")
                print(f"   (при first_k = {first_k_bits} эта последовательность не достигается)")
            else:
                # Пробуем другие k
                found = False
                for k in range(2, 7):
                    first_k, forbidden = find_forbidden_sequence(table, k)
                    if forbidden:
                        first_k_bits = format(first_k, f'0{k}b')
                        print(f"f_{j+1}: найден запрет длины {k}: '{forbidden}'")
                        print(f"   (при first_k = {first_k_bits} эта последовательность не достигается)")
                        found = True
                        break
                if not found:
                    print(f"f_{j+1}: не сильно-равновероятна, но запрет не найден (ошибка в is_strongly_balanced?)")

# ЛР3.1) Построение спектра Уолша-Адамара
def walsh_hadamard_spectrum(func):
    # Вычисляет спектр Уолша-Адамара для булевой функции.
    # func: список из 64 значений 0/1 (таблица истинности)

    n = 6
    size = 1 << n
    
    # 0 → +1, 1 → -1
    f = [1 if val == 0 else -1 for val in func]
    
    # Преобразование Адамара (бабочка)
    step = 1
    while step < size:
        for i in range(0, size, step * 2):
            for j in range(i, i + step):
                u = f[j]
                v = f[j + step]
                f[j] = u + v
                f[j + step] = u - v
        step <<= 1
    
    # Спектр = результат (без деления)
    return f


def analyze_all_spectrums(g):
    #Анализирует спектры для всех f1...f6 с полным выводом.
    tables = [[(val >> (5 - j)) & 1 for val in g] for j in range(6)]
    print("\nСпектр Уолша-Адамара")
    
    for j, table in enumerate(tables):
        W = walsh_hadamard_spectrum(table)
        
        print(f"\nf_{j+1}:")
        print(f"{'ω (bin)':<12} | {'W(ω)':<8} | {'W(ω)/64':<12} | {'Δ = -64*W/64':<15}")
        # Полный вывод всех 64 коэффициентов
        for omega in range(64):
            omega_bin = format(omega, '06b')
            w = W[omega]
            w_norm = w / 64
            delta = -w  # так как Δ = -64 * (w/64) = -w
            print(f"{omega_bin} | {w:6d} | {w_norm:10.4f} | {delta:6d}")
        # Статистика
        non_zero = [w for w in W if w != 0]
        zero_count = 64 - len(non_zero)
        print(f"Нулевых коэффициентов: {zero_count}")
        print(f"Ненулевых: {len(non_zero)}")
        # Корреляционная иммунность
        corr_order = 0
        for order in range(1, 7):
            all_zero = True
            for omega in range(1, 64):
                if bin(omega).count('1') <= order:
                    if W[omega] != 0:
                        all_zero = False
                        break
            if all_zero:
                corr_order = order
            else:
                break
        
        is_balanced = (W[0] == 0)
        
        print(f"W(0) = {W[0]} {'(сбалансирована)' if is_balanced else '(несбалансирована)'}")
        print(f"Порядок корреляционной иммунности: {corr_order}")
        
        if is_balanced and corr_order > 0:
            print(f"Эластичность порядка: {corr_order}")
        elif is_balanced:
            print("Сбалансирована, но не корреляционно-иммунна")
        else:
            print("Несбалансирована")


# ЛР3.2) Наилучшее линейное приближение

def best_linear_approximation(func):
    """
        best_omega: ω, дающий максимальную корреляцию
        best_prob: вероятность совпадения (дробь)
        w_max: максимальное значение |W(ω)|
        best_linear: строка с линейной функцией
    """
    n = 6
    size = 1 << n
    
    # Вычисляем спектр
    W = walsh_hadamard_spectrum(func)
    
    # Ищем максимальное |W(ω)| (для ω ≠ 0 обычно)
    max_val = 0
    best_omega = 0
    
    for omega in range(size):
        if abs(W[omega]) > max_val:
            max_val = abs(W[omega])
            best_omega = omega
    
    w_max = max_val
    
    # Вероятность наилучшего приближения
    # P = 1/2 + W_max / 2^(n+1) = 1/2 + W_max / 128
    prob = 0.5 + w_max / 128
    
    # Дробное представление: числитель/64
    # P = (32 + W_max/2) / 64
    numerator = 32 + w_max // 2
    prob_fraction = f"{numerator}/64"
    
    # Определяем знак и тип линейной функции
    w_sign = W[best_omega]
    
    # Получаем линейную функцию в читаемом виде
    linear_terms = []
    for i in range(n):
        if (best_omega >> (n - 1 - i)) & 1:
            linear_terms.append(f"x{i+1}")
    
    linear_func = " ⊕ ".join(linear_terms) if linear_terms else "0"
    
    if w_sign > 0:
        best_linear = f"f ≈ {linear_func}"
    else:
        best_linear = f"f ≈ {linear_func} ⊕ 1"
    
    return {
        'omega': best_omega,
        'omega_bin': format(best_omega, f'0{n}b'),
        'w_max': w_max,
        'probability': prob,
        'prob_fraction': prob_fraction,
        'linear_func': linear_func,
        'sign': w_sign,
        'best_linear': best_linear
    }

def print_best_approximations(g):
    # Вывод наилучших приближений

    tables = [[(val >> (5 - j)) & 1 for val in g] for j in range(6)]
    
    print("\nНаилучшее приближение:")

    
    results = []
    for j, table in enumerate(tables):
        W = walsh_hadamard_spectrum(table)
        
        # Ищем максимальное |W(ω)|
        w_max = max(abs(w) for w in W)
        
        # Вероятность = (32 + W_max/2) / 64
        numerator = 32 + w_max // 2
        results.append(f"{numerator}/64")
        
        print(f"f_{j+1}: {numerator}/64  (W_max = {w_max})")
    
    print("Итоговая таблица:")
    print("| " + " | ".join(results) + " |")

# ЛР3.3-4) Автокорреляционная функция Cor_f(u) и Бент-функция

def autocorrelation_classic(func):
    """
    Cor_f(u) = Σ (-1)^{f(x) ⊕ f(x ⊕ u)}
    Возвращает:
        список значений Cor_f(u) для u от 0 до 63
    """
    n = 6
    size = 1 << n
    
    # Преобразуем 0/1 в +1/-1 для удобства
    f = [1 if val == 0 else -1 for val in func]
    
    cor = []
    for u in range(size):
        val = 0
        for x in range(size):
            x_xor_u = x ^ u
            val += f[x] * f[x_xor_u]
        cor.append(val)
    
    return cor

def autocorrelation_by_spectrum(func):
    """
    Вычисление автокорреляции через спектр Уолша-Адамара (быстрее).
    Cor_f(u) = (1/2^n) * Σ (-1)^{u·ω} * |W(ω)|^2
    """
    n = 6
    size = 1 << n
    
    # Спектр Уолша-Адамара
    W = walsh_hadamard_spectrum(func)
    
    # Квадраты спектра
    W2 = [w * w for w in W]
    
    # Обратное преобразование Адамара
    cor = W2[:]
    step = 1
    while step < size:
        for i in range(0, size, step * 2):
            for j in range(i, i + step):
                u = cor[j]
                v = cor[j + step]
                cor[j] = u + v
                cor[j + step] = u - v
        step <<= 1
    
    # Нормировка
    cor = [val // size for val in cor]
    
    return cor

def autocorrelation(g):

    tables = [[(val >> (5 - j)) & 1 for val in g] for j in range(6)]
    
    print("\nАвтокорреляция Cor_f(u) И Бент-функция")
    
    print(f"\n{'Функция':<8} | {'max|Cor_f(u)| (u≠0)':<20} | {'Бент-функция?'}")
    print("-" * 60)
    
    for j, table in enumerate(tables):
        cor = autocorrelation_by_spectrum(table)
        max_cor = max(abs(cor[u]) for u in range(1, 64))
        is_bent = all(cor[u] == 0 for u in range(1, 64))
        
        bent_str = "ДА" if is_bent else "НЕТ"
        print(f"f_{j+1}     | {max_cor:20d} | {bent_str}")

    print("Бент-функция — это Cor_f(u)=0 для всех u≠0")
    print("(плоская автокорреляция, максимальная нелинейность)")

# ЛР3.5) Определение k-устойчивости

def find_k_stability(g):
    # Определяет k-устойчивость для всех f1...f6.

    tables = [[(val >> (5 - j)) & 1 for val in g] for j in range(6)]
    
    print("\nОпределение k-устойчивости")
    
    for j, table in enumerate(tables):
        # Спектр
        W = walsh_hadamard_spectrum(table)
        
        # Ищем максимальное k
        k = 0
        for order in range(1, 7):
            all_zero = True
            for omega in range(1, 64):
                if bin(omega).count('1') <= order:
                    if W[omega] != 0:
                        all_zero = False
                        break
            if all_zero:
                k = order
            else:
                break
        
        print(f"f_{j+1}: k = {k} (k-устойчивая)")



# Лабораторная работа №1    
g = generate()
print("Случайная подстановка g: V_6 → V_6")
print("g(x) = ", g)

print("Вектора значений в виде x_1...x_6 g(x) f_1...f_6:")
VecOfVal(g)

weights = hamming_weight(g)
print("Веса Хэмминга: ", weights)

print(f"g = {g[:10]}...\n")
compute_zhegalkin(g, verbose=True)

analyze_all(g)

# Лабораторная работа №2
print_balance_analysis(weights)

analyze_strong_balance(g)

find_all_forbidden_sequences(g)

# Лабораторная работа №3
analyze_all_spectrums(g)

print_best_approximations(g)

autocorrelation(g)

find_k_stability(g)



