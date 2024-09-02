import { CoreModule } from "../core-module";
import { CosmosInputNode, CosmosInputLink } from "../../types";
export declare class ForceManyBodyQuadtree<N extends CosmosInputNode, L extends CosmosInputLink> extends CoreModule<N, L> {
    private randomValuesFbo;
    private levelsFbos;
    private clearLevelsCommand;
    private calculateLevelsCommand;
    private quadtreeCommand;
    private quadtreeLevels;
    create(): void;
    initPrograms(): void;
    run(): void;
    destroy(): void;
}
