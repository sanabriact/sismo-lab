export interface FlatNode {
    id: number;
    key: [number, number, number];
    height: number;
    leftChildId: number | null;
    rightChildId: number | null;
    parentId: number | null;
}