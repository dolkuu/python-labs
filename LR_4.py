import secrets
import time
from typing import List, Tuple, Dict

# Генерируем случайную подстановку на 256 элементах
def generate_byte_sbox() -> List[int]:
    """Генерирует случайный обратимый S-блок 8×8 бит."""
    sbox = list(range(256))
    for i in range(len(sbox) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        sbox[i], sbox[j] = sbox[j], sbox[i]
    return sbox

# Фиксируем S-блок для воспроизводимости
SBOX = generate_byte_sbox()
INV_SBOX = [0] * 256
for i, val in enumerate(SBOX):
    INV_SBOX[val] = i


def encrypt_byte(pt_byte: int, key_byte: int, sbox: List[int]) -> int:
    """
    Шифрование одного байта.
    Алгоритм: pt ⊕ key → S-box → результат
    """
    return sbox[pt_byte ^ key_byte]


def encrypt_block(plaintext: int, key: int, sbox: List[int]) -> int:
    """
    Шифрование 64-битного блока (8 байт).
    Каждый байт обрабатывается независимо с соответствующим байтом ключа.
    """
    result = 0
    for pos in range(8):
        pt_byte = (plaintext >> (pos * 8)) & 0xFF
        key_byte = (key >> (pos * 8)) & 0xFF
        ct_byte = encrypt_byte(pt_byte, key_byte, sbox)
        result |= (ct_byte << (pos * 8))
    return result

def attack_64bit_key(pairs: List[Tuple[int, int]], sbox: List[int]) -> Tuple[int, Dict]:
    """
    Восстанавливает 64-битный ключ по известным парам (открытый текст, шифртекст).
    Принцип: каждый байт ключа восстанавливается независимо.
    Для каждой позиции байта перебираем 256 вариантов.
    Сложность: 8 * 256 * число_пар
    """
    start_time = time.time()

    print("ВОССТАНОВЛЕНИЕ КЛЮЧА ПО ПАРАМ ОТ/ШТ")
    
    recovered_key = 0
    total_checks = 0
    results = []
    
    for pos in range(8):  # 8 байт в 64-битном ключе
        print(f"\n Поиск байта ключа {pos}")
        
        valid_candidates = []
        
        for cand in range(256):  # перебор всех значений байта
            total_checks += len(pairs)
            ok = True
            
            for pt, ct in pairs:
                # Берём байт открытого текста в позиции pos
                pt_byte = (pt >> (pos * 8)) & 0xFF
                # Берём байт шифртекста в позиции pos
                ct_byte = (ct >> (pos * 8)) & 0xFF
                
                # Проверяем: SBOX[pt_byte ⊕ cand] == ct_byte ?
                if encrypt_byte(pt_byte, cand, sbox) != ct_byte:
                    ok = False
                    break
            
            if ok:
                valid_candidates.append(cand)
        
        # Обработка результатов
        if len(valid_candidates) == 0:
            raise RuntimeError(f'Не найден кандидат для байта ключа {pos}')
        
        # Выбираем первый кандидат
        selected = valid_candidates[0]
        recovered_key |= (selected << (pos * 8))
        
        results.append({
            'byte_position': pos,
            'candidate_count': len(valid_candidates),
            'selected_hex': f'{selected:02X}',
            'valid_candidates_hex': ''.join(f'{x:02X}' for x in valid_candidates[:5]) + 
                                     ('...' if len(valid_candidates) > 5 else '')
        })
        
        if len(valid_candidates) == 1:
            print(f"Найден: {selected:02X}")
        else:
            print(f"Найдено {len(valid_candidates)} кандидатов: {[f'{x:02X}' for x in valid_candidates]}")
            print(f"Выбран: {selected:02X}")
    
    end_time = time.time()
    
    stats = {
        'time_ms': (end_time - start_time) * 1000,
        'total_checks': total_checks,
        'num_pairs': len(pairs),
        'formula': f"8·256·{len(pairs)} = {total_checks}",
        'results': results
    }
    
    return recovered_key, stats


def print_results(original_key: int, recovered_key: int, stats: Dict,
                  pairs: List[Tuple[int, int]]):
    
    print("РЕЗУЛЬТАТ АТАКИ")
    
    print(f"\n| {'Параметр':<30} | {'Значение':<30} |")
    print(f"| {'Количество пар ОТ–ШТ':<30} | {len(pairs):<30} |")
    print(f"| {'Исходный ключ':<30} | {original_key:016X} |")
    print(f"| {'Восстановленный ключ':<30} | {recovered_key:016X} |")
    print(f"| {'Ключ восстановлен верно':<30} | {'да' if original_key == recovered_key else 'нет'} |")
    print(f"| {'Проверок кандидатов':<30} | {stats['total_checks']:<30} |")
    print(f"| {'Время атаки, мс':<30} | {stats['time_ms']:.4f} |")
    print(f"| {'Полный перебор':<30} | 2^64 вариантов |")
    print(f"| {'Использованная атака':<30} | {stats['formula']} |")
    
    print("Первые пары открытого и шифрованного текста:")
    print(f"| {'№':<3} | {'ОТ, hex':<16} | {'ШТ, hex':<16} |")
    for i, (pt, ct) in enumerate(pairs[:8]):
        print(f"| {i+1:<3} | {pt:016X} | {ct:016X} |")
    
    print("Количество найденных кандидатов по каждому байту ключа:")
    print(f"| {'Байт ключа':<12} | {'Число кандидатов':<18} | {'Выбранное значение':<18} |")
    
    for res in stats['results']:
        print(f"| {res['byte_position']:<12} | {res['candidate_count']:<18} | {res['selected_hex']:<18} |")
    
    if original_key == recovered_key:
        print("КЛЮЧ ВОССТАНОВЛЕН ПОЛНОСТЬЮ И ВЕРНО!")
    else:
        print("КЛЮЧ НЕ СОВПАДАЕТ (проверьте S-блок и количество пар)")

def main():

    print("АТАКА ПО ИЗВЕСТНЫМ ПАРАМ (64-БИТНЫЙ КЛЮЧ)")
    
    # Генерируем случайный 64-битный ключ
    original_key = secrets.randbits(64)
    print(f"\nСгенерирован секретный ключ: {original_key:016X}")
    
    # Генерируем пары (открытый текст, шифртекст)
    num_pairs = 16
    pairs = []

    for i in range(num_pairs):
        pt = secrets.randbits(64)
        ct = encrypt_block(pt, original_key, SBOX)
        pairs.append((pt, ct))
        
        if i == 0:
            print(f"Первая пара: P = {pt:016X} → C = {ct:016X}")
    
    # Атака
    recovered_key, stats = attack_64bit_key(pairs, SBOX)
    
    # Вывод результатов
    print_results(original_key, recovered_key, stats, pairs)


if __name__ == "__main__":
    main()