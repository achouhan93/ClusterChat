export declare type CosmosInputNode = {
    id: string;
    x?: number;
    y?: number;
};
export declare type CosmosInputLink = {
    source: string;
    target: string;
};
/**
 * @deprecated Will be removed from version 2.0. Use type `CosmosInputNode` instead.
 * @todo Remove deprecated type `InputNode` in version 2.0.
 */
export declare type InputNode = {
    [key: string]: unknown;
    id: string;
    x?: number;
    y?: number;
};
/**
 * @deprecated Will be removed from version 2.0. Use type `CosmosInputLink` instead.
 * @todo Remove deprecated type `InputLink` in version 2.0.
 */
export declare type InputLink = {
    [key: string]: unknown;
    source: string;
    target: string;
};
