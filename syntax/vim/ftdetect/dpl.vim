au BufNewFile,BufRead *.dpl set filetype=dpl

command! -nargs=* Run call RunDPL(<f-args>)

function! RunDPL(...) abort
  " Join all user arguments
  let l:args = join(a:000, ' ')
  let l:file = expand('%:p')

  " Save current file before running
  write

  " Construct the command
<<<<<<< HEAD
  let l:cmd = 'term dpl -skip-non-essential run ' . l:file . ' ' . l:args . "; exit"
=======
  let l:cmd = 'term dpl -skip-non-essential run ' . l:file. ' ' . l:args
>>>>>>> 1.4.8
  echom l:cmd
  execute l:cmd
endfunction

<<<<<<< HEAD
nnoremap <C-e> :call RunDPL()
inoremap <C-e> :call RunDPL()
=======
nnoremap <C-e> :call RunDPL()<CR>
inoremap <C-e> <Esc>:call RunDPL()<CR>
>>>>>>> 1.4.8
