import { CoreModule } from "../core-module";
import { CosmosInputNode, CosmosInputLink } from "../../types";
export declare class ForceManyBody<N extends CosmosInputNode, L extends CosmosInputLink> extends CoreModule<N, L> {
    private randomValuesFbo;
    private levelsFbos;
    private clearLevelsCommand;
    private clearVelocityCommand;
    private calculateLevelsCommand;
    private forceCommand;
    private forceFromItsOwnCentermassCommand;
    private quadtreeLevels;
    create(): void;
    initPrograms(): void;
    run(): void;
    destroy(): void;
}
