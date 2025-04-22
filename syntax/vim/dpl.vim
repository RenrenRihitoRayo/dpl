" Vim syntax file for DPL (Dumb Programming Language)
" Save as ~/.vim/syntax/dpl.vim

if exists("b:current_syntax")
    finish
endif

" Directives
syntax match dplIncludeDirective "&\(define_error\|set_name\|extend\|whatever\|file\|version\|embed\|embed_binary\|\(warn\|dead\)_code_\(disable\|enable\)\|def_fn_\(enable\|disable\)\|save_config\|include\|use\|includec\|extend\|set\|use:luaj\)"

" Keywords
syntax keyword dplKeyword fn md if body match return fallthrough case with default as in is not and or end module thread enum pub export loop while ccall scall smcall scatch smcatch mcatch catch safe stop skip return sched ifmain method pass freturn help wait_for_threads DEFINE_ERROR body pause pycatch ccatch template from_template raise

" Builtins
syntax keyword dplFunction set object new exit del cmd get_time START_TIME STOP_TIME LOG_TIME dump_vars dump_scope dlopen dlclose cdef getc sexec exec new_thread_event

" Constants
syntax keyword dplConstant true false nil none

" Operators
syntax match dplOperator "[-+*/=<>!]=\?"

" Numbers
syntax match dplNumber "\v<\d+(\.\d+)?(e[+-]?\d+)?>"

" Strings

syntax region dplStringI start='{' end='}' contains=dplEscape
syntax region dplString start='\'' end='\'' contains=dplEscape
syntax region dplString start='"' end='"' contains=dplEscape
syntax match dplEscape "\\[nrt\"\\]" contained

" Comments
syntax match dplComment "#.*$" contains=dplTodo
syntax region dplMLComment start="--" end="--" contains=dplTodo
syntax keyword dplTodo TODO FIXME contained

" Define Highlighting
highlight link dplKeyword Keyword
highlight link dplType Type
highlight link dplConstant Constant
highlight link dplOperator Operator
highlight link dplNumber Number
highlight link dplString String
highlight link dplStringI String
highlight link dplEscape SpecialChar
highlight link dplComment Comment
highlight link dplMLComment Comment
highlight link dplTodo Todo
highlight link dplFunction Function

highlight link dplDirective PreProc
highlight link dplIncludeDirective PreProc

let b:current_syntax = "dpl"