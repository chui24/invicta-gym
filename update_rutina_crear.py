import re

with open('templates/gym/rutina_crear.html', 'r') as f:
    content = f.read()

# Replace table with div
content = re.sub(
    r'<!-- Tabla de Ejercicios -->.*?<tbody class="exercises-tbody">\s*<!-- Ejercicios -->\s*</tbody>\s*</table>',
    r'''<!-- Lista de Ejercicios -->
        <div class="p-4">
            <div class="exercises-tbody flex flex-col gap-4">
                <!-- Ejercicios -->
            </div>''',
    content,
    flags=re.DOTALL
)

# Replace template-exercise
content = re.sub(
    r'<template id="template-exercise">.*?</template>',
    r'''<template id="template-exercise">
    <div class="exercise-row group bg-black/40 rounded-xl p-4 border border-white/5 relative">
        <div class="absolute left-0 top-0 bottom-0 w-10 text-gray-600 drag-handle flex items-center justify-center cursor-grab hover:text-white hover:bg-white/5 transition-colors z-20 rounded-l-xl">
            <i class="bi bi-grip-vertical text-lg"></i>
        </div>
        <div class="absolute right-2 top-2">
            <button type="button" class="btn-remove-exercise text-gray-600 hover:text-red-500 transition-colors p-2">
                <i class="bi bi-x-lg"></i>
            </button>
        </div>
        
        <div class="pl-10 pr-8">
            <div class="mb-4">
                <label class="text-[10px] text-gray-500 font-bold uppercase tracking-widest block mb-1">Ejercicio</label>
                <input type="text" class="exercise-name w-full bg-black/50 border border-white/10 text-gray-300 text-sm font-medium rounded-lg px-3 py-2.5 focus:outline-none focus:border-brand-accent transition-colors" placeholder="Ej: Press Militar con Mancuernas">
            </div>
            <div class="grid grid-cols-2 gap-3">
                <div>
                    <label class="text-[10px] text-gray-500 font-bold uppercase tracking-widest block mb-1">Series</label>
                    <input type="text" class="exercise-series w-full bg-black/50 border border-white/10 text-gray-300 text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:border-brand-accent transition-colors text-center" placeholder="Ej: 4">
                </div>
                <div>
                    <label class="text-[10px] text-gray-500 font-bold uppercase tracking-widest block mb-1">Reps</label>
                    <input type="text" class="exercise-details w-full bg-black/50 border border-white/10 text-gray-300 text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:border-brand-accent transition-colors text-center" placeholder="Ej: 10-12">
                </div>
                <input type="hidden" class="exercise-peso" value="">
            </div>
        </div>
    </div>
</template>''',
    content,
    flags=re.DOTALL
)

# Add SortableJS CDN
content = content.replace(
    r'<input type="hidden" id="csrf-token" value="{{ csrf_token }}">',
    r'''<!-- SortableJS -->
<script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
<input type="hidden" id="csrf-token" value="{{ csrf_token }}">'''
)

# Add Sortable initialization
content = content.replace(
    r'''            newCard.querySelector('.btn-remove-day').addEventListener('click', () => {
                newCard.remove();
                saveCurrentWeekState();
                renderActiveWeekDays();
            });
        });
    };''',
    r'''            newCard.querySelector('.btn-remove-day').addEventListener('click', () => {
                newCard.remove();
                saveCurrentWeekState();
                renderActiveWeekDays();
            });

            // Initialize SortableJS
            if (typeof Sortable !== 'undefined') {
                Sortable.create(tbody, {
                    handle: '.drag-handle',
                    animation: 150,
                    ghostClass: 'opacity-30',
                    onEnd: function() {
                        saveCurrentWeekState();
                    }
                });
            } else {
                console.error('SortableJS no está cargado');
            }
        });
    };'''
)

with open('templates/gym/rutina_crear.html', 'w') as f:
    f.write(content)
