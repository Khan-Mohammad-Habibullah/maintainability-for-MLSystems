
# Pseudocode for measuring CBO <sup>ML</sup> and LCC <sup>ML</sup>

## Pseudocode for measuring CBO <sup>ML</sup> 

Initialize `code_files` ← list(project.get_code_files())
Initialize `data_files` ← list(project.get_data_files())

Initialize `files_variables` ← {}
Initialize `files_methods` ← {}
Initialize `connections` ← {}

FOR each `file` in `code_files`

    `files_vars[file]` ← list(file_parser.get_variables(`file`))
    `files_funcs[file]` ← list(file_parser.get_methods(`file`))
    
    FOR each `other_file` in `code_files`
        `connections[file][other_file]` ← false
    END FOR
END FOR

FOR each `file` in `code_files`

    FOR each `line` in `file`
    
        IF `external_method_call` in `line`
            `file_called` = find_called_file(`line`, `files_funcs`)
            `connections[file][file_called]` ← true
        END IF
        
        IF `external_variable_call` in `line`
            `file_called` = find_called_file(`line`, `files_vars`)
            `connections[file][file_called]` ← true
        END IF
        
        FOR each `data_file` in `data_files`
            IF `data_file` in `line`
                `connections[file][data_file]` ← true
            END IF
        END FOR
    END FOR
END FOR

Initialize `CBO` ← {}

FOR each `file` in `code_files`
    `code_edges` = code_edges(`connections`, `file`, `code_files`)
    `data_edges` = data_edges(`connections`, `file`, `data_files`)
    `CBO[file]` = `code_edges` + `data_edges`
END FOR



## Pseudocode for measuring LCC <sup>ML</sup>

Initialize `code_files` ← list(project.get_code_files())
Initialize `data_files` ← list(project.get_data_files())

FOR each `file` in `code_files`

    Initialize `func_vars` ← {}
    Initialize `func_lib_funcs` ← {}
    Initialize `func_data` ← {}

    FOR each `line` in `file`

        IF `method` in `line`
            `used_vars` = get_used_vars(`method`)
            `func_vars[method]` = [`used_vars`]
            `used_lib_funcs` = get_used_lib_funcs(`method`)
            `func_lib_funcs[method]` = [`used_lib_funcs`]
            `called_data_files` = get_called_data(`method`)
            `func_data[method]` = [`called_data_files`]
        END IF
    END FOR
END FOR

`used_params` = union(`func_vars`, `func_lib_funcs`, `func_data`)
`graph` ← create_graph(`used_params`)

`connections_per_func` ← `graph.get_reachable_neighbours()`

`n` = len(`file_methods.keys()`)
`unique_pairs` = n(n-1)/2

`nr_connected_pairs` ← 0

`explored_connections` = []
FOR `func` in `connections_per_func`
    FOR `other_func` in `connections_per_func`

        IF `other_func` in `connections_per_func[func]`
            IF `other_func` not in `explored_connections`

                `nr_connected_pairs` ++
            END IF
        END IF
    END FOR
    `explored_connections.append(func)`
END FOR

IF `nr_unique_pairs` ≠ 0
    `LCC` ← `nr_connected_pairs` / `unique_pairs`
ELSE
    `LCC` ← 1
END IF

