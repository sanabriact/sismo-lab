/* 
    This function returns the seism id into the format SIS-000000N
*/

export function toFormatId(id: number) {
    return `SIS-${id.toString().padStart(6, "0")}`;
}