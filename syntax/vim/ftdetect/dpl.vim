au BufNewFile,BufRead *.dpl set filetype=dpl

command! -nargs=* Run call RunDPL(<f-args>)

function! RunDPL(...) abort
  " Join all user arguments
  let l:args = join(a:000, ' ')
  let l:file = expand('%:p')

  " Save current file before running
  write

  " Construct the command
  let l:cmd = 'term dpl -skip-non-essential run ' . l:file . ' ' . l:args . "; exit"
  echom l:cmd
  execute l:cmd
endfunction

nnoremap <C-e> :call RunDPL()
inoremap <C-e> :call RunDPL()