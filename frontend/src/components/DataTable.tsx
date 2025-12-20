import React from 'react';
import {
    useReactTable,
    getCoreRowModel,
    getPaginationRowModel,
    getSortedRowModel,
    getFilteredRowModel,
    flexRender,
    ColumnDef,
    SortingState,
} from '@tanstack/react-table';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUpDown } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface DataTableProps<TData> {
    data: TData[];
    columns: ColumnDef<TData, any>[];
    pageSize?: number;
}

export function DataTable<TData>({ data, columns, pageSize = 10 }: DataTableProps<TData>) {
    const [sorting, setSorting] = React.useState<SortingState>([]);
    const [globalFilter, setGlobalFilter] = React.useState('');

    const table = useReactTable({
        data,
        columns,
        state: {
            sorting,
            globalFilter,
        },
        onSortingChange: setSorting,
        onGlobalFilterChange: setGlobalFilter,
        getCoreRowModel: getCoreRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        initialState: {
            pagination: {
                pageSize,
            },
        },
    });

    return (
        <div className="space-y-4">
            {/* Search Input */}
            <div className="flex items-center gap-2">
                <input
                    value={globalFilter ?? ''}
                    onChange={e => setGlobalFilter(e.target.value)}
                    className="px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-200 w-full max-w-sm focus:ring-2 focus:ring-cyan-500 outline-none"
                    placeholder="Search all columns..."
                />
            </div>

            <div className="rounded-xl border border-slate-700 bg-slate-900/50 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-slate-800/50 border-b border-slate-700">
                            {table.getHeaderGroups().map(headerGroup => (
                                <tr key={headerGroup.id}>
                                    {headerGroup.headers.map(header => (
                                        <th key={header.id} className="px-4 py-3 text-xs font-semibold text-cyan-400 uppercase tracking-wider">
                                            {header.isPlaceholder ? null : (
                                                <div
                                                    className={cn(
                                                        "flex items-center gap-2",
                                                        header.column.getCanSort() && "cursor-pointer select-none"
                                                    )}
                                                    onClick={header.column.getToggleSortingHandler()}
                                                >
                                                    {flexRender(header.column.columnDef.header, header.getContext())}
                                                    {header.column.getCanSort() && <ArrowUpDown className="w-3 h-3 opacity-50" />}
                                                </div>
                                            )}
                                        </th>
                                    ))}
                                </tr>
                            ))}
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {table.getRowModel().rows.map(row => (
                                <tr key={row.id} className="hover:bg-slate-800/30 transition-colors">
                                    {row.getVisibleCells().map(cell => (
                                        <td key={cell.id} className="px-4 py-3 text-sm text-slate-300 whitespace-nowrap">
                                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-2 text-slate-400 text-sm">
                <div className="flex items-center gap-2">
                    <span>Page</span>
                    <strong className="text-slate-200">
                        {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
                    </strong>
                </div>
                <div className="flex items-center gap-1">
                    <button
                        className="p-1 px-2 rounded hover:bg-slate-800 disabled:opacity-30"
                        onClick={() => table.setPageIndex(0)}
                        disabled={!table.getCanPreviousPage()}
                    >
                        <ChevronsLeft className="w-4 h-4" />
                    </button>
                    <button
                        className="p-1 px-2 rounded hover:bg-slate-800 disabled:opacity-30"
                        onClick={() => table.previousPage()}
                        disabled={!table.getCanPreviousPage()}
                    >
                        <ChevronLeft className="w-4 h-4" />
                    </button>
                    <button
                        className="p-1 px-2 rounded hover:bg-slate-800 disabled:opacity-30"
                        onClick={() => table.nextPage()}
                        disabled={!table.getCanNextPage()}
                    >
                        <ChevronRight className="w-4 h-4" />
                    </button>
                    <button
                        className="p-1 px-2 rounded hover:bg-slate-800 disabled:opacity-30"
                        onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                        disabled={!table.getCanNextPage()}
                    >
                        <ChevronsRight className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
