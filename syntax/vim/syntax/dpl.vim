" Vim syntax file for DPL (Dumb Programming Language)
" Save as ~/.vim/syntax/dpl.vim

" Directives
syntax match dplIncludeDirective "&\(define_error\|set_name\|extend\|whatever\|file\|version\|embed\|embed_binary\|\(warn\|dead\)_code_\(disable\|enable\)\|def_fn_\(enable\|disable\)\|save_config\|include\|use\|includec\|extend\|set\|use:luaj\)"

" Keywords
syntax keyword dplKeyword fallthrough as in is not and or export catch safe stop skip pass help DEFINE_ERROR pycatch ecatch raise local setref set cmd use_luaj use dec inc on_new_scope on_pop_scope 

" - Keywords that indent
syntax match keyword_indent "\<\(dict\|list\|keyword_indent\|string\|string::static\|switch::static\|fn::static\|fn\|if\|match\|case\|with\|default\|module\|while\|sched\|ifmain\|method\|switch\|begin\|enum\|loop\|for\)\>"
" - Keywords that dedent
syntax keyword keyword_dedent end

" Builtins
syntax keyword dplFunction object new exit del cmd get_time START_TIME STOP_TIME LOG_TIME dump_vars dump_scope dlopen dlclose cdef getc sexec exec new_thread_event

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
syntax region dplString start='\'' end='\'' contains=dplEscape,dplInterpolated
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
    " Get previous non-blank line number and its content
    let prev_lnum = prevnonblank(lnum - 1)
    let line = getline(prev_lnum)

    " Get syntax group of previous line's last character
    let col_prev = strlen(line)
    if col_prev == 0
        let col_prev = 1
    endif
    let syn_id = synID(prev_lnum, col_prev, 1)
    let syn_name = synIDattr(syn_id, "name")
    echom syn_name, line

    " Check for indent keyword on previous line
    if syn_name =~# 'keyword_indent'
        return indent(prev_lnum) + &shiftwidth
    endif

    if syn_name =~# 'keyword_dedent'
        call setline(prev_lnum, repeat(' ', target_indent) . substitute(line_text, '^\s*', '', ''))
        return indent(lnum) - &shiftwidth
    endif

    " Default: same indent as previous line
    return indent(prev_lnum)
endfunction

setlocal indentexpr=GetMyIndent()
setlocal autoindent
set shiftwidth=4
let b:current_syntax = "dpl"
