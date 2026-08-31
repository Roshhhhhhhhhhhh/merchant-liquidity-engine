import React from 'react'
import { cn } from '@/utils/cn'

interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {
  children: React.ReactNode
}

export const Table: React.FC<TableProps> = ({ children, className, ...props }) => (
  <div className="w-full overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-fintech-card">
    <table className={cn('w-full text-left text-xs border-collapse', className)} {...props}>
      {children}
    </table>
  </div>
)

export const TableHeader: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  children,
  className,
  ...props
}) => (
  <thead className={cn('bg-slate-50/90 border-b border-slate-200 text-slate-600 uppercase font-semibold text-[11px] tracking-wider', className)} {...props}>
    {children}
  </thead>
)

export const TableBody: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  children,
  className,
  ...props
}) => (
  <tbody className={cn('divide-y divide-slate-100 text-slate-800', className)} {...props}>
    {children}
  </tbody>
)

export const TableRow: React.FC<React.HTMLAttributes<HTMLTableRowElement>> = ({
  children,
  className,
  ...props
}) => (
  <tr className={cn('hover:bg-slate-50/70 transition-colors group', className)} {...props}>
    {children}
  </tr>
)

export const TableHead: React.FC<React.ThHTMLAttributes<HTMLTableCellElement>> = ({
  children,
  className,
  ...props
}) => (
  <th className={cn('py-3 px-4 font-semibold text-slate-700 whitespace-nowrap', className)} {...props}>
    {children}
  </th>
)

export const TableCell: React.FC<React.TdHTMLAttributes<HTMLTableCellElement>> = ({
  children,
  className,
  ...props
}) => (
  <td className={cn('py-3.5 px-4 whitespace-nowrap tabular-nums text-slate-700', className)} {...props}>
    {children}
  </td>
)
