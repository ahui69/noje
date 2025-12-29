# ETAP 4 — DESIGN SYSTEM

## Motywy
- Domyślny dark: bg `#0b0c10`, panele `#111218`, akcent `#8b5cf6`, tekst `#e5e7eb`.
- Light opcjonalny: można włączyć przez usunięcie klasy `dark` na `<html>` (Tailwind darkMode=class).

## Komponenty
- Button: klasy Tailwind `px-3 py-2 rounded font-semibold`, wariant primary `bg-accent text-white`, secondary `border border-subtle`.
- Input/Textarea: `bg-subtle border border-subtle rounded px-3 py-2 text-white focus:border-accent`.
- Modal/Drawer: nieużyte w MVP; można użyć panelu `bg-panel border border-subtle rounded shadow-xl`.
- Dropdown: lista `bg-panel border-subtle rounded shadow`.
- Toast: w MVP alert(), docelowo fixed stack `bottom-4 right-4` z kartami `bg-panel border border-subtle`.
- Skeleton: `animate-pulse bg-subtle/60 rounded`.
- MessageBubble: kontener `p-4 rounded-lg border`, rola user = border-subtle/40, assistant = border-subtle bg-subtle/60.
- CodeBlock: renderowany przez `rehype-highlight`, przycisk "Kopiuj" w prawym górnym rogu bubble.
- AttachmentChip: `px-2 py-1 text-xs rounded bg-subtle text-gray-200 flex items-center gap-2` + przycisk ✕.
- SidebarItem: `px-3 py-2 rounded-md hover:bg-subtle/60`, aktywny ma border `border-subtle/80`.

## Typografia i spacing
- Body: Tailwind `text-sm` w głównych treściach, `text-xs` dla metadanych.
- Headery: h1 `text-2xl font-bold`, h2 `text-xl font-semibold`.
- Spacing: sekcje główne `p-6`, karty `p-4`, odstępy w listach `space-y-4`.

## Dostępność
- Focus rings: `focus:outline-none focus:ring-2 focus:ring-accent/70` na elementach formularza.
- Keyboard nav: textarea obsługuje Enter=send, Shift+Enter=nowa linia; przyciski mają wyraźny focus.
- Kontrast: dark theme z jasnym tekstem, linki i akcje mają `hover` stan.
