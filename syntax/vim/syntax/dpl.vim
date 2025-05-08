" Vim syntax file for DPL (Dumb Programming Language)
" Save as ~/.vim/syntax/dpl.vim

if exists("b:current_syntax")
    finish
endif

" Directives
syntax match dplIncludeDirective "&\(define_error\|set_name\|extend\|whatever\|file\|version\|embed\|embed_binary\|\(warn\|dead\)_code_\(disable\|enable\)\|def_fn_\(enable\|disable\)\|save_config\|include\|use\|includec\|extend\|set\|use:luaj\)"

" Keywords
syntax keyword dplKeyword fallthrough as in is not and or export ccall scall smcall scatch smcatch mcatch catch safe stop skip pass help wait_for_threads DEFINE_ERROR pycatch ccatch raise break_point break_off local

" - Keywords that indent
syntax keyword keyword_indent fn if match case with default module thread pub while sched ifmain method switch begin enum loop for
" - Keywords that dedent
syntax keyword keyword_dedent freturn return end

" Builtins
syntax keyword dplFunction set object tc_register new exit del cmd get_time START_TIME STOP_TIME LOG_TIME dump_vars dump_scope dlopen dlclose cdef getc sexec exec new_thread_event

" Constants
syntax keyword dplConstant true false nil none

" Types
" syntax keyword dplType t_int t_str t_float t_dict t_set t_list t_tuple t_PyException PyNone
syntax match dplType ":types.\(int\|float\|test\)"
syntax match dplType "\v:types\.[^\s,()\[\]@+-/*!]+"

" Operators
syntax match dplOperator "[-+*/=<>!]=\?"
syntax match dplOperator "=>\|->"

" Numbers
syntax match dplNumber "\v<\d+(\.\d+)?>"

" Strings

syntax region dplStringI start='{' end='}' contains=dplEscape
syntax region dplString start='\'' end='\'' contains=dplEscape contains=dplInterpolated
syntax region dplString start='"' end='"' contains=dplEscape
syntax match dplEscape "\\[nrt\"'\\]" contained
syntax match dplInterpolated "\v\$\{[^\}]+\}" contained

" Comments
syntax match dplComment "#.*$" contains=dplTodo
syntax region dplMLComment start="--" end="--" contains=dplTodo
syntax keyword dplTodo TODO FIXME contained

" Define Highlighting
highlight link dplKeyword Keyword
highlight link keyword_indent Keyword
highlight link keyword_dedent Keyword
highlight link dplType Type
highlight link dplConstant Constant
highlight link dplOperator Operator
highlight link dplNumber Number
highlight link dplString String
highlight link dplStringI String
highlight link dplEscape SpecialChar
highlight link dplInterpolated SpecialChar
highlight link dplComment Comment
highlight link dplMLComment Comment
highlight link dplTodo Todo
highlight link dplFunction Function

highlight link dplDirective PreProc
highlight link dplIncludeDirective PreProc

function! GetMyIndent()
    let lnum = v:lnum
    let line = getline(lnum)

    " Get syntax group of previous line
    let syn_id = synID(lnum - 1, 1, 1)
    let syn_name = synIDattr(syn_id, "name")

    if syn_name =~# 'keyword_indent'
        return indent(lnum - 1) + &shiftwidth
    elseif syn_name =~# 'keyword_dedent'
        return indent(lnum - 1) - &shiftwidth
    endif

    return indent(lnum - 2)
endfunction

setlocal indentexpr=GetMyIndent()

let b:current_syntax = "dpl"
