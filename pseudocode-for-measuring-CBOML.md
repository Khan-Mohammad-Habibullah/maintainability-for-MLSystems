```Python

\State \textbf{Initialize} code\_files $\leftarrow$ list(project.get\_code\_files())
\State \textbf{Initialize} data\_files $\leftarrow$ list(project.get\_data\_files())

\State \textbf{Initialize} files\_variables $\leftarrow$ \{\}

 \State \textbf{Initialize} files\_methods $\leftarrow$ \{\}

 \State \textbf{Initialize} connections $\leftarrow$ \{\}
\For{each file in code\_files}

    \State files\_vars[file] $\leftarrow$ list(file\_parser.get\_variables(file))
    \State files\_funcs[file] $\leftarrow$ list(file\_parser.get\_methods(file))
    \For{each other\_file in code\_files}

        \State connections[file][other\_file] $\leftarrow$ \texttt{false}
    \EndFor
 \EndFor


\For{each file in code\_files}

    \For{each line in file}
        \If {external\_method\_call in line}
            \State file\_called = find\_called\_file(line,files\_funcs)
            \State connections[file][file\_called] $\leftarrow$ true
        \EndIf
        \If {external\_variable\_call in line}
            \State file\_called = find\_called\_file(line,files\_vars)
            \State connections[file][file\_called] $\leftarrow$ true
        \EndIf
        \For{data\_file in data\_files}
            \If {data\_file in line}
                \State connections[file][data\_file] $\leftarrow$ true
            \EndIf
        \EndFor                 
    \EndFor
\EndFor


\State \textbf{Initialize} CBO $\leftarrow$ \{\}
\For{each file in code\_files}
    \State code\_edges = code\_edges(connections, file, code\_files)
    \State data\_edges = data\_edges(connections, file, data\_files)
    \State CBO[file] = code\_edges + data\_edges
\EndFor